from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from services.meta_ads_service import meta_ads

logger = logging.getLogger(__name__)
router = APIRouter()

class CampaignCreate(BaseModel):
    name: str
    objective: str
    budget: float
    daily_budget: Optional[float] = None

class CampaignMonitoring(BaseModel):
    campaign_id: str
    profit_margin: float
    max_cpa_ratio: float = 0.8

@router.post("/campaign/create")
async def create_campaign(data: CampaignCreate):
    """Create a new Meta Ads campaign."""
    try:
        campaign = await meta_ads.create_campaign(data.dict())
        if campaign:
            return {"status": "success", "campaign": campaign}
        else:
            raise HTTPException(status_code=400, detail="Failed to create campaign")
    except Exception as e:
        logger.error(f"Campaign creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaign/{campaign_id}/metrics")
async def get_campaign_metrics(campaign_id: str):
    """Get campaign metrics and calculate CPA."""
    try:
        metrics = await meta_ads.get_campaign_metrics(campaign_id)
        if metrics:
            return {
                "status": "success",
                "campaign_id": campaign_id,
                "metrics": metrics,
                "cpa": metrics.get("calculated_cpa", 0)
            }
        else:
            raise HTTPException(status_code=404, detail="Campaign not found")
    except Exception as e:
        logger.error(f"Get metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaign/{campaign_id}/pause")
async def pause_campaign(campaign_id: str):
    """Pause a campaign."""
    try:
        success = await meta_ads.pause_campaign(campaign_id)
        if success:
            return {"status": "success", "message": f"Campaign {campaign_id} paused"}
        else:
            raise HTTPException(status_code=400, detail="Failed to pause campaign")
    except Exception as e:
        logger.error(f"Pause campaign error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaign/{campaign_id}/resume")
async def resume_campaign(campaign_id: str):
    """Resume a campaign."""
    try:
        success = await meta_ads.resume_campaign(campaign_id)
        if success:
            return {"status": "success", "message": f"Campaign {campaign_id} resumed"}
        else:
            raise HTTPException(status_code=400, detail="Failed to resume campaign")
    except Exception as e:
        logger.error(f"Resume campaign error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaign/monitor")
async def monitor_campaign_cpa(data: CampaignMonitoring, background_tasks: BackgroundTasks):
    """Monitor campaign CPA and pause if it exceeds profit margin."""
    try:
        metrics = await meta_ads.get_campaign_metrics(data.campaign_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Campaign not found")

        spend = float(metrics.get("spend", 0))
        cpa = metrics.get("calculated_cpa", 0)
        max_acceptable_cpa = data.profit_margin * data.max_cpa_ratio

        if cpa > max_acceptable_cpa:
            logger.warning(f"Campaign {data.campaign_id} CPA (₹{cpa:.2f}) exceeds max (₹{max_acceptable_cpa:.2f})")
            background_tasks.add_task(meta_ads.pause_campaign, data.campaign_id)
            return {
                "status": "paused",
                "reason": "CPA exceeded profit margin",
                "cpa": cpa,
                "max_acceptable_cpa": max_acceptable_cpa,
                "spend": spend
            }
        else:
            return {
                "status": "active",
                "cpa": cpa,
                "max_acceptable_cpa": max_acceptable_cpa,
                "spend": spend,
                "message": "Campaign performing within acceptable CPA"
            }
    except Exception as e:
        logger.error(f"Campaign monitoring error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
