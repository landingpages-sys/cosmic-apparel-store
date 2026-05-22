import httpx
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

META_API_VERSION = "v18.0"
META_ACCESS_TOKEN = os.getenv("META_ADS_ACCESS_TOKEN")
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID")

class MetaAdsService:
    def __init__(self):
        self.access_token = META_ACCESS_TOKEN
        self.account_id = META_AD_ACCOUNT_ID
        self.base_url = f"https://graph.instagram.com/{META_API_VERSION}"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def get_campaign_metrics(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign metrics including spend, conversions, and CPA."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/{campaign_id}/insights",
                    params={
                        "fields": "spend,actions,action_values,impressions,clicks,cpc,cpm",
                        "access_token": self.access_token
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    if data:
                        metrics = data[0]
                        spend = float(metrics.get("spend", 0))
                        conversions = sum([action.get("value", 0) for action in metrics.get("actions", []) if action.get("action_type") == "purchase"])

                        cpa = spend / conversions if conversions > 0 else 0
                        metrics["calculated_cpa"] = cpa
                        return metrics
                    return None
                else:
                    logger.error(f"Failed to get campaign metrics: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Error getting campaign metrics: {str(e)}")
                return None

    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a campaign."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{campaign_id}",
                    json={
                        "status": "PAUSED",
                        "access_token": self.access_token
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    logger.info(f"Campaign {campaign_id} paused")
                    return True
                else:
                    logger.error(f"Failed to pause campaign: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Error pausing campaign: {str(e)}")
                return False

    async def resume_campaign(self, campaign_id: str) -> bool:
        """Resume a campaign."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{campaign_id}",
                    json={
                        "status": "ACTIVE",
                        "access_token": self.access_token
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    logger.info(f"Campaign {campaign_id} resumed")
                    return True
                else:
                    logger.error(f"Failed to resume campaign: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Error resuming campaign: {str(e)}")
                return False

    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new campaign."""
        async with httpx.AsyncClient() as client:
            try:
                payload = {**campaign_data, "access_token": self.access_token}
                response = await client.post(
                    f"{self.base_url}/act_{self.account_id}/campaigns",
                    json=payload,
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    logger.info(f"Campaign created")
                    return response.json()
                else:
                    logger.error(f"Failed to create campaign: {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Error creating campaign: {str(e)}")
                return None

meta_ads = MetaAdsService()
