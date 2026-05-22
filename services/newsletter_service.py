import httpx
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")
MAILCHIMP_LIST_ID = os.getenv("MAILCHIMP_LIST_ID")
MAILCHIMP_SERVER = os.getenv("MAILCHIMP_SERVER", "us1")

class NewsletterService:
    def __init__(self):
        self.api_key = MAILCHIMP_API_KEY
        self.list_id = MAILCHIMP_LIST_ID
        self.server = MAILCHIMP_SERVER
        self.base_url = f"https://{self.server}.api.mailchimp.com/3.0"
        self.headers = {
            "Authorization": f"apikey {self.api_key}",
            "Content-Type": "application/json"
        }

    async def subscribe_email(self, email: str, merge_fields: Optional[Dict[str, Any]] = None) -> bool:
        """Subscribe email to newsletter."""
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "email_address": email,
                    "status": "subscribed",
                    "timestamp_signup": datetime.utcnow().isoformat() + "Z"
                }
                if merge_fields:
                    payload["merge_fields"] = merge_fields

                response = await client.post(
                    f"{self.base_url}/lists/{self.list_id}/members",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    logger.info(f"Email {email} subscribed to newsletter")
                    return True
                else:
                    logger.error(f"Failed to subscribe email: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Error subscribing email: {str(e)}")
                return False

    async def send_welcome_email(self, email: str) -> bool:
        """Send welcome email to new subscriber."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/lists/{self.list_id}/segments",
                    headers=self.headers,
                    json={
                        "name": f"Welcome_{email}",
                        "options": {
                            "match": "any",
                            "conditions": [
                                {
                                    "condition_type": "EmailDomain",
                                    "field": "email_address",
                                    "op": "contains",
                                    "value": email
                                }
                            ]
                        }
                    },
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    logger.info(f"Welcome email sent to {email}")
                    return True
                else:
                    logger.error(f"Failed to send welcome email: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Error sending welcome email: {str(e)}")
                return False

    async def unsubscribe_email(self, email: str) -> bool:
        """Unsubscribe email from newsletter."""
        async with httpx.AsyncClient() as client:
            try:
                import hashlib
                email_hash = hashlib.md5(email.lower().encode()).hexdigest()
                response = await client.post(
                    f"{self.base_url}/lists/{self.list_id}/members/{email_hash}/actions/delete",
                    headers=self.headers,
                    timeout=30
                )
                if response.status_code == 204:
                    logger.info(f"Email {email} unsubscribed")
                    return True
                else:
                    logger.error(f"Failed to unsubscribe email: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Error unsubscribing email: {str(e)}")
                return False

newsletter = NewsletterService()
