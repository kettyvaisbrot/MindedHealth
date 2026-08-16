"""
Internal service JWT validator for ai_microservice.

Architecture context:
  Django is the external trust boundary. User JWTs are validated at Django and
  never forwarded here. Django issues a short-lived internal service JWT
  (token_type='internal_service', aud includes 'ai-service', exp=60s) signed
  with INTERNAL_JWT_PRIVATE_KEY (RS256). ai_microservice holds only the
  corresponding INTERNAL_JWT_PUBLIC_KEY and can verify tokens but never issue
  them. The token reaching this service was forwarded unchanged by
  insights_service — it was never re-issued.
"""
import os

import jwt

# Loaded once at module import. Both values must be present in the environment
# before this service starts. INTERNAL_JWT_PUBLIC_KEY uses the same \n-escaping
# convention as Django's settings.py: real newlines are stored as \n literals
# in .env / Kubernetes Secrets, and restored here with .replace('\\n', '\n').
INTERNAL_JWT_PUBLIC_KEY: str = os.getenv("INTERNAL_JWT_PUBLIC_KEY", "").replace("\\n", "\n")
INTERNAL_JWT_ISSUER: str = os.getenv("INTERNAL_JWT_ISSUER", "django-api")

# This service's own identity — the value that must appear in the 'aud' claim
# of every internal token accepted here. Hardcoded: only tokens issued for
# this specific service should be usable by this service.
_AUDIENCE = "ai-service"


def validate_internal_jwt(token: str) -> dict:
    """
    Validate an internal service JWT issued by Django (possibly forwarded by
    insights_service unchanged).

    Checks (in order, all enforced by PyJWT unless noted):
      1. RS256 signature — verified against INTERNAL_JWT_PUBLIC_KEY
      2. Expiration      — exp must be in the future
      3. Audience        — 'ai-service' must appear in the aud claim
      4. Issuer          — iss must equal INTERNAL_JWT_ISSUER ('django-api')
      5. token_type      — must equal 'internal_service' (checked after decode)

    Args:
        token: The raw JWT string from the Authorization header (without 'Bearer ').

    Returns:
        The decoded payload dict containing sub, role, caller, token_type, etc.

    Raises:
        jwt.exceptions.InvalidSignatureError : signature does not match the public key
        jwt.exceptions.ExpiredSignatureError : token has expired
        jwt.exceptions.InvalidAudienceError  : 'ai-service' is not in the aud claim
        jwt.exceptions.InvalidIssuerError    : iss claim does not match INTERNAL_JWT_ISSUER
        jwt.exceptions.DecodeError           : token is structurally malformed
        jwt.exceptions.InvalidTokenError     : token_type claim is absent or not 'internal_service'
    """
    payload = jwt.decode(
        token,
        INTERNAL_JWT_PUBLIC_KEY,
        algorithms=["RS256"],
        audience=_AUDIENCE,
        issuer=INTERNAL_JWT_ISSUER,
    )

    if payload.get("token_type") != "internal_service":
        raise jwt.exceptions.InvalidTokenError(
            "token_type must be 'internal_service'"
        )

    return payload
