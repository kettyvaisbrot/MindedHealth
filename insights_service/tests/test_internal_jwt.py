"""
Tests for insights_service.app.auth.internal_jwt.validate_internal_jwt.

No running services required. RSA key pairs are generated on the fly so
tests are fully self-contained. No Django dependency.

Coverage:
  - valid token                → returns payload with expected claims
  - wrong signing key          → InvalidSignatureError
  - expired token              → ExpiredSignatureError
  - wrong audience             → InvalidAudienceError
  - wrong issuer               → InvalidIssuerError
  - wrong token_type value     → InvalidTokenError
  - absent token_type claim    → InvalidTokenError
"""
import uuid
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from app.auth.internal_jwt import validate_internal_jwt


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_rsa_pair():
    """Return (private_pem_str, public_pem_str) for a fresh RSA-2048 key pair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


def _make_token(
    private_pem: str,
    *,
    audience: str = "insights-service",
    issuer: str = "django-api",
    token_type: str = "internal_service",
    lifetime_seconds: int = 60,
    include_token_type: bool = True,
    sub: str = "42",
    role: str = "therapist",
):
    now = datetime.now(tz=timezone.utc)
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": sub,
        "role": role,
        "caller": "django-api",
        "iat": now,
        "exp": now + timedelta(seconds=lifetime_seconds),
        "jti": str(uuid.uuid4()),
    }
    if include_token_type:
        payload["token_type"] = token_type
    return jwt.encode(payload, private_pem, algorithm="RS256")


def _patch_validator(public_pem: str, issuer: str = "django-api"):
    """Context manager that replaces the module-level constants in the validator."""
    return patch.multiple(
        "app.auth.internal_jwt",
        INTERNAL_JWT_PUBLIC_KEY=public_pem,
        INTERNAL_JWT_ISSUER=issuer,
    )


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def key_pair():
    return _make_rsa_pair()


@pytest.fixture(scope="module")
def other_key_pair():
    """Unrelated key pair — tokens must be rejected when verified against this public key."""
    return _make_rsa_pair()


# ── tests ─────────────────────────────────────────────────────────────────────

def test_valid_token_returns_payload(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem)
    with _patch_validator(public_pem):
        payload = validate_internal_jwt(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "therapist"
    assert payload["token_type"] == "internal_service"
    assert payload["aud"] == "insights-service"
    assert payload["iss"] == "django-api"


def test_wrong_signing_key_raises_invalid_signature(key_pair, other_key_pair):
    private_pem, _ = key_pair
    _, wrong_public_pem = other_key_pair
    token = _make_token(private_pem)
    with _patch_validator(wrong_public_pem):
        with pytest.raises(jwt.exceptions.InvalidSignatureError):
            validate_internal_jwt(token)


def test_expired_token_raises_expired_signature(key_pair):
    private_pem, public_pem = key_pair
    # lifetime=-1 → exp = iat - 1s → already past at decode time
    token = _make_token(private_pem, lifetime_seconds=-1)
    with _patch_validator(public_pem):
        with pytest.raises(jwt.exceptions.ExpiredSignatureError):
            validate_internal_jwt(token)


def test_wrong_audience_raises_invalid_audience(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem, audience="ai-service")
    with _patch_validator(public_pem):
        with pytest.raises(jwt.exceptions.InvalidAudienceError):
            validate_internal_jwt(token)


def test_wrong_issuer_raises_invalid_issuer(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem, issuer="rogue-service")
    with _patch_validator(public_pem, issuer="django-api"):
        with pytest.raises(jwt.exceptions.InvalidIssuerError):
            validate_internal_jwt(token)


def test_wrong_token_type_raises_invalid_token(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem, token_type="access")
    with _patch_validator(public_pem):
        with pytest.raises(jwt.exceptions.InvalidTokenError):
            validate_internal_jwt(token)


def test_missing_token_type_raises_invalid_token(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem, include_token_type=False)
    with _patch_validator(public_pem):
        with pytest.raises(jwt.exceptions.InvalidTokenError):
            validate_internal_jwt(token)
