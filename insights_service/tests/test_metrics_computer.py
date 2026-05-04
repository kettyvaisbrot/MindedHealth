import pytest
from app.services.metrics_computer import compute_metrics, compute_correlations


@pytest.fixture
def empty_logs():
    return {
        "food": [],
        "sport": [],
        "sleep": [],
        "meetings": [],
        "medications": [],
        "felt_off": [],
    }


# ── compute_metrics ──────────────────────────────────────────────────────────

class TestMedicationAdherence:
    def test_full_adherence(self, empty_logs):
        empty_logs["medications"] = [
            {"taken": True},
            {"taken": True},
            {"taken": True},
        ]
        metrics = compute_metrics(empty_logs)
        assert metrics["medication_adherence_percent"] == 100.0

    def test_partial_adherence(self, empty_logs):
        empty_logs["medications"] = [
            {"taken": True},
            {"taken": True},
            {"taken": False},
        ]
        metrics = compute_metrics(empty_logs)
        assert metrics["medication_adherence_percent"] == 66.7

    def test_all_missed(self, empty_logs):
        empty_logs["medications"] = [{"taken": False}, {"taken": False}]
        metrics = compute_metrics(empty_logs)
        assert metrics["medication_adherence_percent"] == 0

    def test_no_medication_logs(self, empty_logs):
        metrics = compute_metrics(empty_logs)
        assert metrics["medication_adherence_percent"] == 0

    def test_missed_and_taken_counts_are_also_correct(self, empty_logs):
        empty_logs["medications"] = [
            {"taken": True},
            {"taken": False},
            {"taken": False},
        ]
        metrics = compute_metrics(empty_logs)
        assert metrics["taken_doses"] == 1
        assert metrics["missed_doses"] == 2


class TestMeetingMetrics:
    def test_avg_positivity(self, empty_logs):
        empty_logs["meetings"] = [
            {"positivity_rating": 4},
            {"positivity_rating": 2},
            {"positivity_rating": 5},
        ]
        metrics = compute_metrics(empty_logs)
        assert metrics["avg_meeting_positivity"] == 3.7

    def test_avg_positivity_no_meetings(self, empty_logs):
        metrics = compute_metrics(empty_logs)
        assert metrics["avg_meeting_positivity"] == 0

    def test_avg_positivity_skips_none_ratings(self, empty_logs):
        empty_logs["meetings"] = [
            {"positivity_rating": 4},
            {"positivity_rating": None},
            {"positivity_rating": 2},
        ]
        metrics = compute_metrics(empty_logs)
        assert metrics["avg_meeting_positivity"] == 3.0

    def test_positive_meetings_threshold_is_3(self, empty_logs):
        empty_logs["meetings"] = [
            {"positivity_rating": 5},
            {"positivity_rating": 3},
            {"positivity_rating": 2},
            {"positivity_rating": 1},
        ]
        metrics = compute_metrics(empty_logs)
        assert metrics["positive_meetings"] == 2

    def test_positive_meetings_zero_when_all_low(self, empty_logs):
        empty_logs["meetings"] = [
            {"positivity_rating": 1},
            {"positivity_rating": 2},
        ]
        metrics = compute_metrics(empty_logs)
        assert metrics["positive_meetings"] == 0

    def test_positive_meetings_no_meetings(self, empty_logs):
        metrics = compute_metrics(empty_logs)
        assert metrics["positive_meetings"] == 0


class TestSleepMetrics:
    def test_avg_sleep_hours(self, empty_logs):
        empty_logs["sleep"] = [
            {"hours": 8.0, "woke_up_during_night": False},
            {"hours": 6.0, "woke_up_during_night": True},
        ]
        metrics = compute_metrics(empty_logs)
        assert metrics["avg_sleep_hours"] == 7.0
        assert metrics["nights_awakened"] == 1

    def test_sleep_skips_entries_with_no_hours(self, empty_logs):
        empty_logs["sleep"] = [
            {"hours": None, "woke_up_during_night": False},
            {"hours": 7.0, "woke_up_during_night": False},
        ]
        metrics = compute_metrics(empty_logs)
        assert metrics["avg_sleep_hours"] == 7.0

    def test_no_sleep_logs(self, empty_logs):
        metrics = compute_metrics(empty_logs)
        assert metrics["avg_sleep_hours"] == 0
        assert metrics["nights_awakened"] == 0


class TestFeltOffMetrics:
    def test_felt_off_count_and_intensity(self, empty_logs):
        empty_logs["felt_off"] = [
            {"had_moment": True, "intensity": 4},
            {"had_moment": True, "intensity": 2},
            {"had_moment": False, "intensity": 5},  # not counted
        ]
        metrics = compute_metrics(empty_logs)
        assert metrics["felt_off_count"] == 2
        assert metrics["avg_felt_off_intensity"] == 3.0

    def test_no_felt_off_moments(self, empty_logs):
        empty_logs["felt_off"] = [{"had_moment": False, "intensity": 3}]
        metrics = compute_metrics(empty_logs)
        assert metrics["felt_off_count"] == 0
        assert metrics["avg_felt_off_intensity"] == 0


# ── compute_correlations ──────────────────────────────────────────────────────

class TestComputeCorrelations:
    def test_missed_meds_and_felt_off_produces_message(self):
        metrics = {
            "missed_doses": 3,
            "felt_off_count": 2,
            "avg_sleep_hours": 7.5,
            "days_exercised": 4,
        }
        result = compute_correlations({}, metrics)
        assert "missed" in result.lower() or "medication" in result.lower()

    def test_low_sleep_produces_message(self):
        metrics = {
            "missed_doses": 0,
            "felt_off_count": 0,
            "avg_sleep_hours": 5.0,
            "days_exercised": 4,
        }
        result = compute_correlations({}, metrics)
        assert "sleep" in result.lower()

    def test_low_exercise_produces_message(self):
        metrics = {
            "missed_doses": 0,
            "felt_off_count": 0,
            "avg_sleep_hours": 8.0,
            "days_exercised": 1,
        }
        result = compute_correlations({}, metrics)
        assert "exercised" in result.lower() or "activity" in result.lower()

    def test_all_good_returns_default_message(self):
        metrics = {
            "missed_doses": 0,
            "felt_off_count": 0,
            "avg_sleep_hours": 8.0,
            "days_exercised": 5,
        }
        result = compute_correlations({}, metrics)
        assert result == "No significant correlations detected."

    def test_multiple_issues_all_appear(self):
        metrics = {
            "missed_doses": 2,
            "felt_off_count": 3,
            "avg_sleep_hours": 4.5,
            "days_exercised": 0,
        }
        result = compute_correlations({}, metrics)
        assert len(result.split("\n")) >= 3
