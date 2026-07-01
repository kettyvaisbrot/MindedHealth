import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

INSIGHTS_URL = "/insights/api/insights/"
_FAKE_TOKEN = "test.internal.jwt"


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _empty_logs():
    return {k: [] for k in ["food", "sport", "sleep", "meetings", "medications", "felt_off"]}


# Patch generate_internal_service_token for every test in this file.
# Tests here cover payload shape and failure handling, not token issuance.
# Without this patch the real function would fail — no RSA key is configured
# in the test environment.
@pytest.fixture(autouse=True)
def mock_token_issuer():
    with patch(
        "insights.views.generate_internal_service_token",
        return_value=_FAKE_TOKEN,
    ) as mock:
        yield mock


# DRF stores throttle_classes as a class attribute on APIView at import time,
# so overriding Django settings alone is not enough. Patching the class
# attribute directly is the only reliable way to disable throttling in tests
# when Redis is not running locally.
@pytest.fixture(autouse=True)
def disable_throttle(monkeypatch):
    from rest_framework.views import APIView
    monkeypatch.setattr(APIView, "throttle_classes", [])


# ── authentication ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_unauthenticated_request_is_rejected():
    response = APIClient().get(INSIGHTS_URL)
    assert response.status_code in (401, 403)


# ── successful flow ───────────────────────────────────────────────────────────

@patch("insights.views.requests.post")
@patch("insights.views.fetch_user_logs")
@pytest.mark.django_db
def test_returns_insight_from_service(mock_fetch, mock_post, auth_client):
    mock_fetch.return_value = _empty_logs()

    mock_response = MagicMock()
    mock_response.json.return_value = {"insights": "You had a great week!"}
    mock_post.return_value = mock_response

    response = auth_client.get(INSIGHTS_URL)

    assert response.status_code == 200
    assert response.data == {"insights": "You had a great week!"}


@patch("insights.views.requests.post")
@patch("insights.views.fetch_user_logs")
@pytest.mark.django_db
def test_payload_contains_user_id(mock_fetch, mock_post, auth_client, user):
    mock_fetch.return_value = _empty_logs()
    mock_post.return_value = MagicMock(json=lambda: {"insights": "ok"})

    auth_client.get(INSIGHTS_URL)

    payload = mock_post.call_args.kwargs["json"]
    assert payload["user_id"] == user.id


@patch("insights.views.requests.post")
@patch("insights.views.fetch_user_logs")
@pytest.mark.django_db
def test_payload_contains_all_log_keys(mock_fetch, mock_post, auth_client):
    mock_fetch.return_value = _empty_logs()
    mock_post.return_value = MagicMock(json=lambda: {"insights": "ok"})

    auth_client.get(INSIGHTS_URL)

    payload = mock_post.call_args.kwargs["json"]
    expected_keys = {"food", "sport", "sleep", "meetings", "medications", "felt_off"}
    assert expected_keys == set(payload["logs"].keys())


@patch("insights.views.requests.post")
@patch("insights.views.fetch_user_logs")
@pytest.mark.django_db
def test_payload_is_json_serializable(mock_fetch, mock_post, auth_client):
    import json
    mock_fetch.return_value = _empty_logs()
    mock_post.return_value = MagicMock(json=lambda: {"insights": "ok"})

    auth_client.get(INSIGHTS_URL)

    payload = mock_post.call_args.kwargs["json"]
    # If this raises, the payload contains non-serializable types (e.g. datetime.time)
    json.dumps(payload)


# ── serialization correctness ─────────────────────────────────────────────────

@patch("insights.views.requests.post")
@patch("insights.views.fetch_user_logs")
@pytest.mark.django_db
def test_medication_log_serialized_with_taken_boolean(mock_fetch, mock_post, auth_client):
    med_taken = MagicMock()
    med_taken.date = "2026-04-28"
    med_taken.time_taken = "08:00:00"   # non-null → taken = True

    med_missed = MagicMock()
    med_missed.date = "2026-04-27"
    med_missed.time_taken = None        # null → taken = False

    mock_fetch.return_value = {**_empty_logs(), "medications": [med_taken, med_missed]}
    mock_post.return_value = MagicMock(json=lambda: {"insights": "ok"})

    auth_client.get(INSIGHTS_URL)

    meds = mock_post.call_args.kwargs["json"]["logs"]["medications"]
    assert meds[0]["taken"] is True
    assert meds[1]["taken"] is False


@patch("insights.views.requests.post")
@patch("insights.views.fetch_user_logs")
@pytest.mark.django_db
def test_sleep_log_serialized_with_hours(mock_fetch, mock_post, auth_client):
    from datetime import time

    sleep_log = MagicMock()
    sleep_log.date = "2026-04-28"
    sleep_log.went_to_sleep_yesterday = time(23, 0)
    sleep_log.wake_up_time = time(7, 0)
    sleep_log.woke_up_during_night = False

    mock_fetch.return_value = {**_empty_logs(), "sleep": [sleep_log]}
    mock_post.return_value = MagicMock(json=lambda: {"insights": "ok"})

    auth_client.get(INSIGHTS_URL)

    sleep = mock_post.call_args.kwargs["json"]["logs"]["sleep"]
    assert sleep[0]["hours"] == 8.0
    assert sleep[0]["went_to_sleep_yesterday"] == "23:00:00"
    assert sleep[0]["wake_up_time"] == "07:00:00"


# ── failure handling ──────────────────────────────────────────────────────────

@patch("insights.views.requests.post")
@patch("insights.views.fetch_user_logs")
@pytest.mark.django_db
def test_returns_503_when_insights_service_is_down(mock_fetch, mock_post, auth_client):
    import requests as req
    mock_fetch.return_value = _empty_logs()
    mock_post.side_effect = req.RequestException("Connection refused")

    response = auth_client.get(INSIGHTS_URL)

    assert response.status_code == 503
    assert "unavailable" in response.data["insights"].lower()


@patch("insights.views.requests.post")
@patch("insights.views.fetch_user_logs")
@pytest.mark.django_db
def test_503_response_includes_insights_key(mock_fetch, mock_post, auth_client):
    import requests as req
    mock_fetch.return_value = _empty_logs()
    mock_post.side_effect = req.RequestException("Timeout")

    response = auth_client.get(INSIGHTS_URL)

    assert "insights" in response.data


# ── PR #8: internal JWT header verification ───────────────────────────────────

@patch("insights.views.requests.post")
@patch("insights.views.fetch_user_logs")
@pytest.mark.django_db
def test_authorization_bearer_header_is_sent(mock_fetch, mock_post, auth_client):
    mock_fetch.return_value = _empty_logs()
    mock_post.return_value = MagicMock(json=lambda: {"insights": "ok"})

    auth_client.get(INSIGHTS_URL)

    headers = mock_post.call_args.kwargs["headers"]
    assert headers.get("Authorization") == f"Bearer {_FAKE_TOKEN}"


@patch("insights.views.requests.post")
@patch("insights.views.fetch_user_logs")
@pytest.mark.django_db
def test_x_internal_key_not_sent(mock_fetch, mock_post, auth_client):
    mock_fetch.return_value = _empty_logs()
    mock_post.return_value = MagicMock(json=lambda: {"insights": "ok"})

    auth_client.get(INSIGHTS_URL)

    headers = mock_post.call_args.kwargs["headers"]
    assert "X-Internal-Key" not in headers


@patch("insights.views.requests.post")
@patch("insights.views.fetch_user_logs")
@pytest.mark.django_db
def test_token_issued_with_correct_arguments(mock_fetch, mock_post, auth_client, user, mock_token_issuer):
    mock_fetch.return_value = _empty_logs()
    mock_post.return_value = MagicMock(json=lambda: {"insights": "ok"})

    auth_client.get(INSIGHTS_URL)

    mock_token_issuer.assert_called_once_with(
        user_id=user.id,
        user_role=user.role,
        audience="insights-service",
    )
