from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
import hmac
import hashlib
import json
from services.shopify_service import shopify
from services.printify_service import printify

logger = logging.getLogger(__name__)
router = APIRouter()

SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET")

class OrderWebhook(BaseModel):
    id: int
    email: str
    financial_status: str
    fulfillment_status: str
    line_items: List[Dict[str, Any]]
    shipping_address: Dict[str, Any]
    total_price: str

def verify_shopify_webhook(request_body: bytes, hmac_header: str) -> bool:
    """Verify Shopify webhook signature."""
    hash_object = hmac.new(
        SHOPIFY_WEBHOOK_SECRET.encode(),
        request_body,
        hashlib.sha256
    )
    computed_hmac = hash_object.digest()
    import base64
    return hmac.compare_digest(computed_hmac, base64.b64decode(hmac_header))

@router.post("/webhook/order-create")
async def handle_order_webhook(
    data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    x_shopify_hmac_sha256: str = Header(None)
):
    """Handle new order webhook from Shopify and create Printify order."""
    try:
        if not verify_shopify_webhook(json.dumps(data).encode(), x_shopify_hmac_sha256):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        order_id = data.get("id")
        email = data.get("email")
        line_items = data.get("line_items", [])
        shipping_address = data.get("shipping_address", {})

        order_data = {
            "order_id": str(order_id),
            "customer_email": email,
            "shipping_address": shipping_address,
            "line_items": line_items
        }

        background_tasks.add_task(submit_to_printify, order_data)
        return {
            "status": "received",
            "order_id": order_id,
            "message": "Order received and queued for fulfillment"
        }
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def submit_to_printify(order_data: Dict[str, Any]):
    """Background task to submit order to Printify."""
    try:
        result = await printify.create_print_order(order_data)
        if result:
            logger.info(f"Order {order_data['order_id']} submitted to Printify")
        else:
            logger.error(f"Failed to submit order {order_data['order_id']} to Printify")
    except Exception as e:
        logger.error(f"Printify submission error: {str(e)}")

@router.get("/sync")
async def sync_all_orders(background_tasks: BackgroundTasks):
    """Sync all pending Shopify orders to Printify."""
    try:
        orders = await shopify.get_orders(status="unfulfilled")
        if orders:
            for order in orders:
                order_data = {
                    "order_id": str(order.get("id")),
                    "customer_email": order.get("email"),
                    "shipping_address": order.get("shipping_address", {}),
                    "line_items": order.get("line_items", [])
                }
                background_tasks.add_task(submit_to_printify, order_data)
            return {
                "status": "success",
                "orders_queued": len(orders),
                "message": f"{len(orders)} orders queued for fulfillment"
            }
        else:
            return {"status": "success", "orders_queued": 0, "message": "No pending orders"}
    except Exception as e:
        logger.error(f"Order sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}/status")
async def get_order_status(order_id: str):
    """Get order fulfillment status."""
    try:
        status = await printify.get_order_status(order_id)
        if status:
            return {"status": "success", "order": status}
        else:
            raise HTTPException(status_code=404, detail="Order not found")
    except Exception as e:
        logger.error(f"Get order status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

import os
