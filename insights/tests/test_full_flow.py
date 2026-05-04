"""
Full-flow integration test for the insights pipeline.

What runs for real (no mocks):
    - Django authentication
    - Django DB query via fetch_user_logs()
    - Django serialize_logs() — including sleep hours computation and medication boolean
    - insights_service compute_metrics()
    - insights_service compute_correlations()
    - insights_service build_insight_prompt()

What is mocked:
    - Redis (no server required)
    - get_ai_insight() — the HTTP call to ai_microservice / OpenAI

How the HTTP boundary is bridged:
    Django's `requests.post(insights_service_url, ...)` is replaced by an adapter
    that calls the real insights_service ASGI app through FastAPI's TestClient.
    No HTTP server needs to be running.
"""

import pytest
from datetime import date, time, timedelta
from urllib.parse import urlparse
from unittest.mock import patch, MagicMock

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from fastapi.testclient import TestClient as FastAPITestClient

from dashboard.models import (
    FoodLog,
    SportLog,
    SleepingLog,
    Meetings,
    FeltOffLog,
    MedicationIntakeLog,
)

User = get_user_model()
INSIGHTS_URL = "/insights/api/insights/"


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return User.objects.create_user(username="flow_test_user", password="pass")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def logs_in_db(user):
    """Creates one week of synthetic activity logs in the test database."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    FoodLog.objects.create(
        user=user,
        date=today,
        breakfast_ate=True,
        lunch_ate=True,
        dinner_ate=False,
    )
    SportLog.objects.create(
        user=user,
        date=today,
        did_sport=True,
        sport_type="running",
    )
    # SleepingLog.date is auto_now_add — cannot be set manually
    SleepingLog.objects.create(
        user=user,
        went_to_sleep_yesterday=time(23, 0),
        wake_up_time=time(7, 0),
        woke_up_during_night=False,
    )
    Meetings.objects.create(
        user=user,
        date=today,
        positivity_rating=4,
        meeting_type="family",
    )
    FeltOffLog.objects.create(
        user=user,
        date=today,
        had_moment=True,
        intensity=2,
        duration="30 min",
        description="Felt anxious before the meeting",
    )
    # One taken dose, one missed — produces 50% adherence
    MedicationIntakeLog.objects.create(
        user=user,
        medication_ref_id=1,
        date=today,
        time_taken=time(8, 0),
        dose_index=0,
    )
    MedicationIntakeLog.objects.create(
        user=user,
        medication_ref_id=1,
        date=yesterday,
        time_taken=None,        # missed
        dose_index=0,
    )


# ── ASGI adapter ──────────────────────────────────────────────────────────────

def _insights_service_adapter():
    """
    Returns a callable that replaces requests.post() in Django's insights view.

    Instead of making a real HTTP request, it dispatches the call directly
    to the insights_service ASGI app via FastAPI's TestClient.
    The real compute_metrics / prompt_builder / insights_engine all execute.
    """
    from app.main import app as insights_app

    _client = FastAPITestClient(insights_app)

    def adapter(url, json=None, timeout=None, **kwargs):
        path = urlparse(url).path
        raw = _client.post(path, json=json)

        mock_resp = MagicMock()
        mock_resp.status_code = raw.status_code
        mock_resp.json.return_value = raw.json()
        mock_resp.raise_for_status = MagicMock()  # 200 path: no-op
        return mock_resp

    return adapter


# ── tests ─────────────────────────────────────────────────────────────────────

@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
@patch("insights.views.requests.post")
@pytest.mark.django_db
def test_response_contains_insights_key(
    mock_post, mock_ai, mock_redis, auth_client, logs_in_db
):
    mock_redis.get.return_value = None
    mock_ai.return_value = "You had a productive week!"
    mock_post.side_effect = _insights_service_adapter()

    response = auth_client.get(INSIGHTS_URL)

    assert response.status_code == 200
    assert "insights" in response.data


@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
@patch("insights.views.requests.post")
@pytest.mark.django_db
def test_ai_receives_a_non_empty_prompt(
    mock_post, mock_ai, mock_redis, auth_client, logs_in_db
):
    mock_redis.get.return_value = None
    mock_ai.return_value = "AI insight text"
    mock_post.side_effect = _insights_service_adapter()

    auth_client.get(INSIGHTS_URL)

    mock_ai.assert_called_once()
    prompt = mock_ai.call_args.args[0]
    assert isinstance(prompt, str)
    assert len(prompt) > 100   # a real prompt is always substantial


@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
@patch("insights.views.requests.post")
@pytest.mark.django_db
def test_prompt_contains_activity_data_from_db(
    mock_post, mock_ai, mock_redis, auth_client, logs_in_db
):
    """Verifies the full data path: DB → serialize → metrics → prompt."""
    mock_redis.get.return_value = None
    captured = {}

    def capture(prompt):
        captured["prompt"] = prompt
        return "ok"

    mock_ai.side_effect = capture
    mock_post.side_effect = _insights_service_adapter()

    auth_client.get(INSIGHTS_URL)

    prompt = captured["prompt"]
    # Sleep data (went to sleep 23:00, woke at 07:00 → 8 hours)
    assert "8.0" in prompt or "Sleep" in prompt or "🛌" in prompt
    # Sport data
    assert "Sport" in prompt or "🏃" in prompt
    # Food data
    assert "Food" in prompt or "🍽" in prompt


@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
@patch("insights.views.requests.post")
@pytest.mark.django_db
def test_medication_adherence_is_50_percent(
    mock_post, mock_ai, mock_redis, auth_client, logs_in_db
):
    """
    Proves the full serialization chain is correct:
    MedicationIntakeLog.time_taken → serialize_logs (taken boolean)
    → compute_metrics (adherence percent) → prompt.

    We created 1 taken + 1 missed → expect 50.0% in the prompt.
    """
    mock_redis.get.return_value = None
    captured = {}

    def capture(prompt):
        captured["prompt"] = prompt
        return "ok"

    mock_ai.side_effect = capture
    mock_post.side_effect = _insights_service_adapter()

    auth_client.get(INSIGHTS_URL)

    assert "50.0%" in captured["prompt"], (
        f"Expected 50.0% adherence in prompt. Prompt was:\n{captured['prompt']}"
    )


@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
@patch("insights.views.requests.post")
@pytest.mark.django_db
def test_prompt_has_no_none_placeholders(
    mock_post, mock_ai, mock_redis, auth_client, logs_in_db
):
    """
    Catches any metric that fell through as None, which would produce
    broken text like 'Medication adherence: None%' in the AI prompt.
    """
    mock_redis.get.return_value = None
    captured = {}

    def capture(prompt):
        captured["prompt"] = prompt
        return "ok"

    mock_ai.side_effect = capture
    mock_post.side_effect = _insights_service_adapter()

    auth_client.get(INSIGHTS_URL)

    prompt = captured["prompt"]
    assert "None%" not in prompt, "medication_adherence_percent is None in the prompt"
    assert "positivity: None" not in prompt, "avg_meeting_positivity is None in the prompt"
    assert "meetings: None" not in prompt, "positive_meetings is None in the prompt"


@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
@patch("insights.views.requests.post")
@pytest.mark.django_db
def test_insight_text_is_returned_to_django_client(
    mock_post, mock_ai, mock_redis, auth_client, logs_in_db
):
    """Verifies the full return path: AI text → insights_service → Django → client."""
    mock_redis.get.return_value = None
    mock_ai.return_value = "Unique marker: xK9qZ"
    mock_post.side_effect = _insights_service_adapter()

    response = auth_client.get(INSIGHTS_URL)

    assert response.data["insights"] == "Unique marker: xK9qZ"
