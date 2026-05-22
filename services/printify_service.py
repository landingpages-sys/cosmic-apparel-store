import httpx
import logging
import os
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

PRINTIFY_API_BASE = "https://api.printify.com/v1"
PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_KEY")
SHOPIFY_STORE_ID = os.getenv("SHOPIFY_STORE_ID")

class PrintifyService:
    def __init__(self):
        self.api_key = PRINTIFY_API_KEY
        self.base_url = PRINTIFY_API_BASE
        self.store_id = SHOPIFY_STORE_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def sync_products(self, products: list) -> Dict[str, Any]:
        """Sync products from Shopify to Printify."""
        async with httpx.AsyncClient() as client:
            results = []
            for product in products:
                try:
                    response = await client.post(
                        f"{self.base_url}/shops/{self.store_id}/products",
                        headers=self.headers,
                        json=product,
                        timeout=30
                    )
                    if response.status_code in [200, 201]:
                        results.append({"id": product.get("id"), "status": "synced"})
                        logger.info(f"Product {product.get('id')} synced to Printify")
                    else:
                        logger.error(f"Failed to sync product {product.get('id')}: {response.text}")
                        results.append({"id": product.get("id"), "status": "failed", "error": response.text})
                except Exception as e:
                    logger.error(f"Error syncing product {product.get('id')}: {str(e)}")
                    results.append({"id": product.get("id"), "status": "error", "error": str(e)})
            return {"synced": results}

    async def create_print_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a print order in Printify."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/orders",
                    headers=self.headers,
                    json=order_data,
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    logger.info(f"Print order created: {response.json()}")
                    return response.json()
                else:
                    logger.error(f"Failed to create print order: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Error creating print order: {str(e)}")
                return None

    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order status from Printify."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/orders/{order_id}",
                    headers=self.headers,
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get order status: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Error getting order status: {str(e)}")
                return None

    async def get_printify_catalog(self) -> Optional[Dict[str, Any]]:
        """Get available print products from Printify."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/catalog/blueprints",
                    headers=self.headers,
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get catalog: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Error getting catalog: {str(e)}")
                return None

printify = PrintifyService()
