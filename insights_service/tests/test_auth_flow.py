"""
Tests for the dual-mode authentication introduced in PR #7.

The endpoint now tries JWT first, then falls back to X-Internal-Key.
Both paths must accept valid credentials and reject invalid ones.

Matrix:
  ✓ Valid Internal JWT             → 200
  ✓ Valid INTERNAL_API_KEY         → 200
  ✓ Invalid JWT (wrong key)        → 401
  ✓ Expired JWT                    → 401
  ✓ Wrong audience                 → 401
  ✓ Wrong issuer                   → 401
  ✓ Invalid X-Internal-Key         → 401
  ✓ Missing authentication         → 401
"""
import uuid
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_TEST_API_KEY = "test-internal-api-key-pr7"
# Minimal valid log payload — content does not matter for auth tests.
_PAYLOAD = {"user_id": 1, "logs": {k: [] for k in ["food", "sport", "sleep", "meetings", "medications", "felt_off"]}}


# ── RSA key helpers ───────────────────────────────────────────────────────────

def _make_rsa_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
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


@pytest.fixture(scope="module")
def key_pair():
    return _make_rsa_pair()


@pytest.fixture(scope="module")
def other_key_pair():
    return _make_rsa_pair()


def _make_token(
    private_pem: str,
    *,
    audience: str = "insights-service",
    issuer: str = "django-api",
    token_type: str = "internal_service",
    lifetime_seconds: int = 60,
):
    now = datetime.now(tz=timezone.utc)
    return jwt.encode(
        {
            "iss": issuer,
            "aud": audience,
            "sub": "42",
            "role": "therapist",
            "caller": "django-api",
            "token_type": token_type,
            "iat": now,
            "exp": now + timedelta(seconds=lifetime_seconds),
            "jti": str(uuid.uuid4()),
        },
        private_pem,
        algorithm="RS256",
    )


def _jwt_patches(public_pem: str, issuer: str = "django-api"):
    return patch.multiple(
        "app.auth.internal_jwt",
        INTERNAL_JWT_PUBLIC_KEY=public_pem,
        INTERNAL_JWT_ISSUER=issuer,
    )


# ── autouse: mock business logic so auth tests don't hit redis / OpenAI ──────

@pytest.fixture(autouse=True)
def _mock_business_logic():
    with patch("app.services.insights_engine.redis_client") as mock_redis, \
         patch("app.services.insights_engine.get_ai_insight") as mock_ai:
        mock_redis.get.return_value = None
        mock_ai.return_value = "test insight"
        yield


# ── auth matrix ───────────────────────────────────────────────────────────────

def test_valid_internal_jwt_returns_200(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem)
    with _jwt_patches(public_pem), patch("app.api.insights.INTERNAL_API_KEY", _TEST_API_KEY):
        resp = client.post(
            "/api/v1/insights",
            json=_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200


def test_valid_internal_api_key_returns_200():
    with patch("app.api.insights.INTERNAL_API_KEY", _TEST_API_KEY):
        resp = client.post(
            "/api/v1/insights",
            json=_PAYLOAD,
            headers={"X-Internal-Key": _TEST_API_KEY},
        )
    assert resp.status_code == 200


def test_invalid_jwt_wrong_key_returns_401(key_pair, other_key_pair):
    private_pem, _ = key_pair
    _, wrong_public_pem = other_key_pair
    token = _make_token(private_pem)
    with _jwt_patches(wrong_public_pem):
        resp = client.post(
            "/api/v1/insights",
            json=_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401


def test_expired_jwt_returns_401(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem, lifetime_seconds=-1)
    with _jwt_patches(public_pem):
        resp = client.post(
            "/api/v1/insights",
            json=_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401


def test_wrong_audience_returns_401(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem, audience="ai-service")
    with _jwt_patches(public_pem):
        resp = client.post(
            "/api/v1/insights",
            json=_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401


def test_wrong_issuer_returns_401(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem, issuer="rogue-service")
    with _jwt_patches(public_pem, issuer="django-api"):
        resp = client.post(
            "/api/v1/insights",
            json=_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401


def test_invalid_api_key_returns_401():
    with patch("app.api.insights.INTERNAL_API_KEY", _TEST_API_KEY):
        resp = client.post(
            "/api/v1/insights",
            json=_PAYLOAD,
            headers={"X-Internal-Key": "wrong-key"},
        )
    assert resp.status_code == 401


def test_missing_authentication_returns_401():
    with patch("app.api.insights.INTERNAL_API_KEY", _TEST_API_KEY):
        resp = client.post("/api/v1/insights", json=_PAYLOAD)
    assert resp.status_code == 401
