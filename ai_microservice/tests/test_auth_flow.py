"""
Tests for Internal Service JWT authentication on ai_microservice.

The endpoint requires Authorization: Bearer <internal-service-JWT>. This token
is forwarded unchanged by insights_service -- ai_microservice never receives
a token it wasn't handed by an upstream caller, and it never issues its own.
No other authentication mechanism (e.g. X-Internal-Key) is accepted.

Matrix:
  ✓ Valid Internal JWT             → 200
  ✓ Invalid JWT (wrong key)        → 401
  ✓ Expired JWT                    → 401
  ✓ Wrong audience                 → 401
  ✓ Wrong issuer                   → 401
  ✓ Missing Authorization header   → 401
"""
import uuid
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_PAYLOAD = {"prompt": "How was my week?"}


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
    audience: str = "ai-service",
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
        "internal_jwt",
        INTERNAL_JWT_PUBLIC_KEY=public_pem,
        INTERNAL_JWT_ISSUER=issuer,
    )


# ── autouse: mock the OpenAI call so auth tests don't hit the network ────────

@pytest.fixture(autouse=True)
def _mock_business_logic():
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "test insight"
    with patch("main.call_openai_with_retry", return_value=fake_response):
        yield


@pytest.fixture(autouse=True)
def _reset_failure_count():
    import main
    main.failure_count = 0
    yield
    main.failure_count = 0


# ── auth matrix ───────────────────────────────────────────────────────────────

def test_valid_internal_jwt_returns_200(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem)
    with _jwt_patches(public_pem):
        resp = client.post(
            "/generate-insight",
            json=_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200


def test_invalid_jwt_wrong_key_returns_401(key_pair, other_key_pair):
    private_pem, _ = key_pair
    _, wrong_public_pem = other_key_pair
    token = _make_token(private_pem)
    with _jwt_patches(wrong_public_pem):
        resp = client.post(
            "/generate-insight",
            json=_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401


def test_expired_jwt_returns_401(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem, lifetime_seconds=-1)
    with _jwt_patches(public_pem):
        resp = client.post(
            "/generate-insight",
            json=_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401


def test_wrong_audience_returns_401(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem, audience="insights-service")
    with _jwt_patches(public_pem):
        resp = client.post(
            "/generate-insight",
            json=_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401


def test_wrong_issuer_returns_401(key_pair):
    private_pem, public_pem = key_pair
    token = _make_token(private_pem, issuer="rogue-service")
    with _jwt_patches(public_pem, issuer="django-api"):
        resp = client.post(
            "/generate-insight",
            json=_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401


def test_missing_authentication_returns_401():
    resp = client.post("/generate-insight", json=_PAYLOAD)
    assert resp.status_code == 401


def test_multi_audience_token_is_accepted(key_pair):
    """The token Django issues is scoped to both hops (insights-service AND
    ai-service); ai_microservice must accept it via the same forwarded token."""
    private_pem, public_pem = key_pair
    token = _make_token(private_pem, audience=["insights-service", "ai-service"])
    with _jwt_patches(public_pem):
        resp = client.post(
            "/generate-insight",
            json=_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200


def test_x_internal_key_alone_is_no_longer_accepted():
    resp = client.post(
        "/generate-insight",
        json=_PAYLOAD,
        headers={"X-Internal-Key": "whatever-the-old-shared-secret-was"},
    )
    assert resp.status_code == 401
