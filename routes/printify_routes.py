from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import logging
from services.printify_service import printify

logger = logging.getLogger(__name__)
router = APIRouter()

class Product(BaseModel):
    id: str
    title: str
    handle: str
    images: List[Dict[str, Any]]
    variants: List[Dict[str, Any]]

class OrderData(BaseModel):
    order_id: str
    customer_email: str
    shipping_address: Dict[str, Any]
    line_items: List[Dict[str, Any]]

@router.post("/sync-products")
async def sync_products(products: List[Product]):
    """Sync products to Printify."""
    try:
        result = await printify.sync_products([p.dict() for p in products])
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Product sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-order")
async def create_print_order(order_data: OrderData):
    """Create a print order in Printify and submit for fulfillment."""
    try:
        printify_order = await printify.create_print_order(order_data.dict())
        if printify_order:
            return {
                "status": "success",
                "printify_order_id": printify_order.get("id"),
                "message": "Order submitted for printing"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create print order")
    except Exception as e:
        logger.error(f"Print order creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/order-status/{order_id}")
async def get_order_status(order_id: str):
    """Get Printify order status."""
    try:
        status = await printify.get_order_status(order_id)
        if status:
            return {"status": "success", "order": status}
        else:
            raise HTTPException(status_code=404, detail="Order not found")
    except Exception as e:
        logger.error(f"Get order status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/catalog")
async def get_printify_catalog():
    """Get available print products from Printify."""
    try:
        catalog = await printify.get_printify_catalog()
        if catalog:
            return {"status": "success", "products": catalog}
        else:
            raise HTTPException(status_code=400, detail="Failed to fetch catalog")
    except Exception as e:
        logger.error(f"Get catalog error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
