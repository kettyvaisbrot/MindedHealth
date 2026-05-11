import os
import logging
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from app.services.insights_engine import generate_insights

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["insights"])

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


def verify_internal_key(x_internal_key: Optional[str] = Header(None)):
    print("HEADER RECEIVED:", x_internal_key)
    print("EXPECTED:", INTERNAL_API_KEY)
    if not x_internal_key or x_internal_key != INTERNAL_API_KEY:
        logger.warning("Unauthorized request to insights_service: invalid or missing X-Internal-Key")
        raise HTTPException(status_code=401, detail="Unauthorized")


class InsightsRequest(BaseModel):
    user_id: int
    logs: dict


@router.post("/insights")
def insights_endpoint(req: InsightsRequest, x_internal_key: Optional[str] = Header(None)):
    verify_internal_key(x_internal_key)
    insight_text = generate_insights(
        user_id=req.user_id,
        logs=req.logs,
    )
    return {"insights": insight_text}
