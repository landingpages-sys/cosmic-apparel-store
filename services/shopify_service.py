import httpx
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

SHOPIFY_API_VERSION = "2024-01"
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

class ShopifyService:
    def __init__(self):
        self.store = SHOPIFY_STORE
        self.token = SHOPIFY_ACCESS_TOKEN
        self.base_url = f"https://{self.store}.myshopify.com/admin/api/{SHOPIFY_API_VERSION}"
        self.headers = {
            "X-Shopify-Access-Token": self.token,
            "Content-Type": "application/json"
        }

    async def get_orders(self, status: str = "any") -> Optional[list]:
        """Get orders from Shopify."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/orders.json?status={status}",
                    headers=self.headers,
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json().get("orders", [])
                else:
                    logger.error(f"Failed to get orders: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Error getting orders: {str(e)}")
                return None

    async def get_products(self, limit: int = 50) -> Optional[list]:
        """Get products from Shopify."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/products.json?limit={limit}",
                    headers=self.headers,
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json().get("products", [])
                else:
                    logger.error(f"Failed to get products: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Error getting products: {str(e)}")
                return None

    async def create_product(self, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a product in Shopify."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/products.json",
                    headers=self.headers,
                    json={"product": product_data},
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    logger.info(f"Product created: {product_data.get('title')}")
                    return response.json().get("product")
                else:
                    logger.error(f"Failed to create product: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Error creating product: {str(e)}")
                return None

    async def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a product in Shopify."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    f"{self.base_url}/products/{product_id}.json",
                    headers=self.headers,
                    json={"product": product_data},
                    timeout=30
                )
                if response.status_code == 200:
                    logger.info(f"Product {product_id} updated")
                    return response.json().get("product")
                else:
                    logger.error(f"Failed to update product: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Error updating product: {str(e)}")
                return None

shopify = ShopifyService()
