"""
Internal service JWT validator for insights_service.

CURRENT STATUS: infrastructure only — not yet wired into any request handler.
The endpoint in app/api/insights.py still authenticates via INTERNAL_API_KEY
(the X-Internal-Key header). That mechanism is untouched.

NEXT PR: app/api/insights.py will be updated to call validate_internal_jwt()
instead of verify_internal_key(). Once that change is deployed and confirmed
in production, X-Internal-Key / INTERNAL_API_KEY will be removed.

Architecture context:
  Django is the external trust boundary. User JWTs are validated at Django and
  never forwarded here. Django issues a short-lived internal service JWT
  (token_type='internal_service', aud='insights-service', exp=60s) signed with
  INTERNAL_JWT_PRIVATE_KEY (RS256). insights_service holds only the corresponding
  INTERNAL_JWT_PUBLIC_KEY and can verify tokens but never issue them.
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
_AUDIENCE = "insights-service"


def validate_internal_jwt(token: str) -> dict:
    """
    Validate an internal service JWT issued by Django.

    Checks (in order, all enforced by PyJWT unless noted):
      1. RS256 signature — verified against INTERNAL_JWT_PUBLIC_KEY
      2. Expiration      — exp must be in the future
      3. Audience        — aud must equal 'insights-service'
      4. Issuer          — iss must equal INTERNAL_JWT_ISSUER ('django-api')
      5. token_type      — must equal 'internal_service' (checked after decode)

    Args:
        token: The raw JWT string from the Authorization header (without 'Bearer ').

    Returns:
        The decoded payload dict containing sub, role, caller, token_type, etc.

    Raises:
        jwt.exceptions.InvalidSignatureError : signature does not match the public key
        jwt.exceptions.ExpiredSignatureError : token has expired
        jwt.exceptions.InvalidAudienceError  : aud claim is not 'insights-service'
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
