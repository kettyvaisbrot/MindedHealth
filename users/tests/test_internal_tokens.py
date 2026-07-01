"""
Tests for users.internal_tokens.generate_internal_service_token.

No database access. No running services. RSA key pairs are generated on the
fly with cryptography so these tests are fully self-contained.

Coverage:
  - token is decodable with the correct internal public key
  - all required claims are present with correct values
  - each call produces a unique jti
  - token lifetime equals INTERNAL_JWT_LIFETIME_SECONDS exactly
  - token signed with a different key is rejected (InvalidSignatureError)
  - expired token is rejected (ExpiredSignatureError)
  - token presented to the wrong audience is rejected (InvalidAudienceError)
"""
import pytest
import jwt
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from django.test import override_settings

from users.internal_tokens import generate_internal_service_token


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


def _settings(private_pem, public_pem, lifetime=60):
    return override_settings(
        INTERNAL_JWT_PRIVATE_KEY=private_pem,
        INTERNAL_JWT_PUBLIC_KEY=public_pem,
        INTERNAL_JWT_ISSUER='django-api',
        INTERNAL_JWT_LIFETIME_SECONDS=lifetime,
    )


def _decode(token, public_pem, audience='insights-service'):
    return jwt.decode(token, public_pem, algorithms=['RS256'], audience=audience)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def key_pair():
    return _make_rsa_pair()


@pytest.fixture(scope='module')
def other_key_pair():
    """Unrelated key pair — tokens must not be verifiable with this public key."""
    return _make_rsa_pair()


# ── tests ─────────────────────────────────────────────────────────────────────

def test_token_decodable_with_internal_public_key(key_pair):
    private_pem, public_pem = key_pair
    with _settings(private_pem, public_pem):
        token = generate_internal_service_token(
            user_id=42, user_role='therapist', audience='insights-service'
        )
    payload = _decode(token, public_pem)
    assert payload['sub'] == '42'


def test_all_required_claims_present(key_pair):
    private_pem, public_pem = key_pair
    with _settings(private_pem, public_pem):
        token = generate_internal_service_token(
            user_id=7, user_role='patient', audience='insights-service'
        )
    payload = _decode(token, public_pem)

    assert payload['iss'] == 'django-api'
    assert payload['aud'] == 'insights-service'
    assert payload['sub'] == '7'
    assert payload['role'] == 'patient'
    assert payload['caller'] == 'django-api'
    assert payload['token_type'] == 'internal_service'
    assert 'iat' in payload
    assert 'exp' in payload
    assert 'jti' in payload


def test_jti_is_unique_per_call(key_pair):
    private_pem, public_pem = key_pair
    with _settings(private_pem, public_pem):
        t1 = generate_internal_service_token(1, 'therapist', 'insights-service')
        t2 = generate_internal_service_token(1, 'therapist', 'insights-service')
    p1 = _decode(t1, public_pem)
    p2 = _decode(t2, public_pem)
    assert p1['jti'] != p2['jti']


def test_token_lifetime_equals_configured_seconds(key_pair):
    private_pem, public_pem = key_pair
    before = int(datetime.now(tz=timezone.utc).timestamp())
    with _settings(private_pem, public_pem, lifetime=60):
        token = generate_internal_service_token(1, 'therapist', 'insights-service')
    after = int(datetime.now(tz=timezone.utc).timestamp())

    payload = _decode(token, public_pem)
    assert payload['exp'] - payload['iat'] == 60
    assert before <= payload['iat'] <= after


def test_wrong_public_key_raises_invalid_signature(key_pair, other_key_pair):
    private_pem, _ = key_pair
    _, wrong_public_pem = other_key_pair
    with _settings(private_pem, wrong_public_pem):
        token = generate_internal_service_token(1, 'therapist', 'insights-service')
    with pytest.raises(jwt.exceptions.InvalidSignatureError):
        _decode(token, wrong_public_pem)


def test_expired_token_raises_expired_signature(key_pair):
    private_pem, public_pem = key_pair
    # lifetime=-1 → exp = iat - 1s → already expired at decode time
    with _settings(private_pem, public_pem, lifetime=-1):
        token = generate_internal_service_token(1, 'therapist', 'insights-service')
    with pytest.raises(jwt.exceptions.ExpiredSignatureError):
        _decode(token, public_pem)


def test_wrong_audience_raises_invalid_audience(key_pair):
    private_pem, public_pem = key_pair
    with _settings(private_pem, public_pem):
        token = generate_internal_service_token(
            user_id=1, user_role='therapist', audience='insights-service'
        )
    with pytest.raises(jwt.exceptions.InvalidAudienceError):
        _decode(token, public_pem, audience='ai-service')
