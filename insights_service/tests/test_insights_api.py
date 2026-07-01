import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# These tests cover business logic (caching, prompt quality, etc.), not auth.
# _authenticate is bypassed so each test exercises only what it intends to test.
@pytest.fixture(autouse=True)
def _bypass_auth(monkeypatch):
    monkeypatch.setattr("app.api.insights._authenticate", lambda auth: None)


SAMPLE_LOGS = {
    "food": [
        {"date": "2026-04-28", "breakfast_ate": True, "lunch_ate": True, "dinner_ate": True}
    ],
    "sport": [
        {"date": "2026-04-28", "did_sport": True, "sport_type": "running", "other_sport": None}
    ],
    "sleep": [
        {
            "date": "2026-04-28",
            "went_to_sleep_yesterday": "23:00:00",
            "wake_up_time": "07:00:00",
            "woke_up_during_night": False,
            "hours": 8.0,
        }
    ],
    "meetings": [
        {"date": "2026-04-28", "time": "14:00:00", "meeting_type": "family", "positivity_rating": 4}
    ],
    "medications": [
        {"date": "2026-04-28", "taken": True},
        {"date": "2026-04-27", "taken": False},
    ],
    "felt_off": [
        {
            "date": "2026-04-27",
            "had_moment": True,
            "duration": "30 minutes",
            "intensity": 2,
            "description": "Felt anxious",
        }
    ],
}


# ── response structure ────────────────────────────────────────────────────────

@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
def test_endpoint_returns_insights_key(mock_ai, mock_redis):
    mock_redis.get.return_value = None
    mock_ai.return_value = "You had a great week!"

    response = client.post("/api/v1/insights", json={"user_id": 1, "logs": SAMPLE_LOGS})

    assert response.status_code == 200
    assert "insights" in response.json()


@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
def test_endpoint_returns_ai_text_verbatim(mock_ai, mock_redis):
    mock_redis.get.return_value = None
    mock_ai.return_value = "You had a great week!"

    response = client.post("/api/v1/insights", json={"user_id": 1, "logs": SAMPLE_LOGS})

    assert response.json()["insights"] == "You had a great week!"


# ── caching behaviour ─────────────────────────────────────────────────────────

@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
def test_cache_hit_with_matching_hash_skips_ai(mock_ai, mock_redis):
    # Compute the hash that the engine would produce for SAMPLE_LOGS
    import hashlib
    logs_json = json.dumps(SAMPLE_LOGS, sort_keys=True, default=str)
    data_hash = hashlib.sha256(logs_json.encode()).hexdigest()

    mock_redis.get.return_value = json.dumps(
        {"insight": "Cached insight", "data_hash": data_hash}
    )

    response = client.post("/api/v1/insights", json={"user_id": 1, "logs": SAMPLE_LOGS})

    assert response.status_code == 200
    assert response.json()["insights"] == "Cached insight"
    mock_ai.assert_not_called()


@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
def test_cache_hit_with_stale_hash_calls_ai(mock_ai, mock_redis):
    mock_redis.get.return_value = json.dumps(
        {"insight": "Old cached insight", "data_hash": "stale_hash_that_wont_match"}
    )
    mock_ai.return_value = "Fresh AI response"

    response = client.post("/api/v1/insights", json={"user_id": 1, "logs": SAMPLE_LOGS})

    assert response.status_code == 200
    mock_ai.assert_called_once()


@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
def test_result_is_stored_in_redis_on_cache_miss(mock_ai, mock_redis):
    mock_redis.get.return_value = None
    mock_ai.return_value = "New insight"

    client.post("/api/v1/insights", json={"user_id": 1, "logs": SAMPLE_LOGS})

    mock_redis.set.assert_called_once()
    set_args = mock_redis.set.call_args
    stored = json.loads(set_args.args[1])
    assert stored["insight"] == "New insight"
    assert "data_hash" in stored


# ── prompt quality (no None values) ──────────────────────────────────────────

@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
def test_prompt_does_not_contain_none_for_adherence(mock_ai, mock_redis):
    mock_redis.get.return_value = None
    captured = {}

    def capture(prompt):
        captured["prompt"] = prompt
        return "ok"

    mock_ai.side_effect = capture

    client.post("/api/v1/insights", json={"user_id": 1, "logs": SAMPLE_LOGS})

    assert "None%" not in captured["prompt"], (
        "medication_adherence_percent was None in the prompt"
    )


@patch("app.services.insights_engine.redis_client")
@patch("app.services.insights_engine.get_ai_insight")
def test_prompt_does_not_contain_none_for_meeting_positivity(mock_ai, mock_redis):
    mock_redis.get.return_value = None
    captured = {}

    def capture(prompt):
        captured["prompt"] = prompt
        return "ok"

    mock_ai.side_effect = capture

    client.post("/api/v1/insights", json={"user_id": 1, "logs": SAMPLE_LOGS})

    # The line in prompt_builder is: "Avg meeting positivity: {metrics.get('avg_meeting_positivity')}"
    assert "positivity: None" not in captured["prompt"], (
        "avg_meeting_positivity was None in the prompt"
    )


# ── empty logs ────────────────────────────────────────────────────────────────

@patch("app.services.insights_engine.redis_client")
def test_empty_logs_returns_welcome_message_without_calling_ai(mock_redis):
    empty_logs = {k: [] for k in ["food", "sport", "sleep", "meetings", "medications", "felt_off"]}

    with patch("app.services.insights_engine.get_ai_insight") as mock_ai:
        response = client.post("/api/v1/insights", json={"user_id": 1, "logs": empty_logs})
        mock_ai.assert_not_called()

    assert response.status_code == 200
    assert "dashboard" in response.json()["insights"].lower()


# ── health check ──────────────────────────────────────────────────────────────

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
