"""
Internal service JWT issuer.

This module is architecturally separate from users/tokens.py, which customises
the user-facing simplejwt serializer. Nothing here touches Django auth models,
simplejwt, or the user-facing RS256 key pair (JWT_PRIVATE_KEY / JWT_PUBLIC_KEY).

Purpose:
  Django is the external trust boundary. User JWTs are validated once at the
  Django layer and never forwarded to internal services. Instead, Django issues
  a short-lived internal service JWT — signed with a SEPARATE key pair
  (INTERNAL_JWT_PRIVATE_KEY) — that carries the user's identity as a trusted
  assertion and scopes the call to a specific downstream audience.

Downstream FastAPI services (insights_service, ai_microservice) hold only
INTERNAL_JWT_PUBLIC_KEY and verify these internal tokens. They never receive
or verify user-facing JWTs.
"""
import uuid
from datetime import datetime, timezone, timedelta

import jwt
from django.conf import settings


def generate_internal_service_token(user_id: int, user_role: str, audience: str) -> str:
    """
    Return a signed RS256 JWT for a single Django → downstream service call.

    Args:
        user_id:   The authenticated user's primary key (stored as str per JWT spec).
        user_role: The user's role string (e.g. 'therapist', 'patient').
        audience:  The target service name (e.g. 'insights-service', 'ai-service').
                   Downstream services must validate that aud matches their own name.

    The token is signed with settings.INTERNAL_JWT_PRIVATE_KEY (RS256).
    Verification requires settings.INTERNAL_JWT_PUBLIC_KEY — not the user JWT key.
    Lifetime is settings.INTERNAL_JWT_LIFETIME_SECONDS (default 60 seconds).
    """
    now = datetime.now(tz=timezone.utc)
    lifetime = getattr(settings, 'INTERNAL_JWT_LIFETIME_SECONDS', 60)

    payload = {
        'iss': settings.INTERNAL_JWT_ISSUER,
        'aud': audience,
        'sub': str(user_id),
        'role': user_role,
        'caller': 'django-api',
        'token_type': 'internal_service',
        'iat': now,
        'exp': now + timedelta(seconds=lifetime),
        'jti': str(uuid.uuid4()),
    }

    return jwt.encode(payload, settings.INTERNAL_JWT_PRIVATE_KEY, algorithm='RS256')
