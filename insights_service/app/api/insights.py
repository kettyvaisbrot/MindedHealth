from fastapi import APIRouter
from pydantic import BaseModel

from app.services.insights_engine import generate_insights

router = APIRouter(prefix="/api/v1", tags=["insights"])


class InsightsRequest(BaseModel):
    user_id: int
    logs: dict


@router.post("/insights")
def insights_endpoint(req: InsightsRequest):
    insight_text = generate_insights(
        user_id=req.user_id,
        logs=req.logs,
    )
    return {"insights": insight_text}
