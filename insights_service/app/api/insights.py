import logging
import jwt
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from app.services.insights_engine import generate_insights
from app.auth.internal_jwt import validate_internal_jwt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["insights"])


def _authenticate(authorization: Optional[str]) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization[len("Bearer "):]
    try:
        validate_internal_jwt(token)
    except jwt.exceptions.PyJWTError as exc:
        logger.warning("Invalid internal JWT: %s", exc)
        raise HTTPException(status_code=401, detail="Unauthorized")


class InsightsRequest(BaseModel):
    user_id: int
    logs: dict


@router.post("/insights")
def insights_endpoint(
    req: InsightsRequest,
    authorization: Optional[str] = Header(None),
):
    _authenticate(authorization)
    insight_text = generate_insights(
        user_id=req.user_id,
        logs=req.logs,
    )
    return {"insights": insight_text}
