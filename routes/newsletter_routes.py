from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import logging
from services.newsletter_service import newsletter

logger = logging.getLogger(__name__)
router = APIRouter()

class NewsletterSubscription(BaseModel):
    email: EmailStr

@router.post("/subscribe")
async def subscribe_newsletter(data: NewsletterSubscription):
    """Subscribe email to newsletter."""
    try:
        success = await newsletter.subscribe_email(data.email)
        if success:
            await newsletter.send_welcome_email(data.email)
            return {"status": "success", "message": "Successfully subscribed!"}
        else:
            raise HTTPException(status_code=400, detail="Failed to subscribe")
    except Exception as e:
        logger.error(f"Newsletter subscription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/unsubscribe")
async def unsubscribe_newsletter(data: NewsletterSubscription):
    """Unsubscribe email from newsletter."""
    try:
        success = await newsletter.unsubscribe_email(data.email)
        if success:
            return {"status": "success", "message": "Successfully unsubscribed"}
        else:
            raise HTTPException(status_code=400, detail="Failed to unsubscribe")
    except Exception as e:
        logger.error(f"Newsletter unsubscription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
