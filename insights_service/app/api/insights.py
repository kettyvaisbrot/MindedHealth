import os
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

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


def verify_internal_key(x_internal_key: Optional[str] = Header(None)):
    print("HEADER RECEIVED:", x_internal_key)
    print("EXPECTED:", INTERNAL_API_KEY)
    if not x_internal_key or x_internal_key != INTERNAL_API_KEY:
        logger.warning("Unauthorized request to insights_service: invalid or missing X-Internal-Key")
        raise HTTPException(status_code=401, detail="Unauthorized")


def _authenticate(authorization: Optional[str], x_internal_key: Optional[str]) -> None:
    """
    Dual-mode authentication: JWT Bearer token (preferred) with X-Internal-Key fallback.

    If Authorization: Bearer <token> is present, the token is validated via
    validate_internal_jwt(). Any PyJWT exception produces a 401.

    If no Bearer token is present, the request falls through to the existing
    shared-key check via verify_internal_key(). This preserves backward
    compatibility while callers migrate to JWT auth.

    Once all callers send JWT tokens, verify_internal_key() and INTERNAL_API_KEY
    will be removed in a follow-up PR.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):]
        try:
            validate_internal_jwt(token)
        except jwt.exceptions.PyJWTError as exc:
            logger.warning("Invalid internal JWT: %s", exc)
            raise HTTPException(status_code=401, detail="Unauthorized")
        return

    # No Bearer token — fall back to shared key auth.
    verify_internal_key(x_internal_key)


class InsightsRequest(BaseModel):
    user_id: int
    logs: dict


@router.post("/insights")
def insights_endpoint(
    req: InsightsRequest,
    authorization: Optional[str] = Header(None),
    x_internal_key: Optional[str] = Header(None),
):
    _authenticate(authorization, x_internal_key)
    insight_text = generate_insights(
        user_id=req.user_id,
        logs=req.logs,
    )
    return {"insights": insight_text}
