import pytest
from django.contrib.auth.models import User
from dashboard.models import (
    FoodLog,
    SportLog,
    SleepingLog,
    Meetings,
    SeizureLog
)
from datetime import date, time


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="pass123")


def test_food_log_str(user):
    log = FoodLog.objects.create(
        user=user,
        date=date.today(),
        breakfast_ate=True,
        breakfast_time=time(8, 30),
        lunch_ate=True,
        lunch_time=time(13, 0),
        dinner_ate=False,
    )
    assert str(log) == f"Food Log on {log.date} for {user.username}"
    assert log.breakfast_ate is True
    assert log.breakfast_time == time(8, 30)


def test_sport_log_str(user):
    log = SportLog.objects.create(
        user=user,
        date=date.today(),
        did_sport=True,
        sport_type="running",
        sport_time=time(10, 0)
    )
    assert "Sport Log on" in str(log)
    assert log.sport_type == "running"
    assert log.sport_time == time(10, 0)


def test_sleeping_log_str(user):
    log = SleepingLog.objects.create(
        user=user,
        went_to_sleep_yesterday=time(23, 0),
        wake_up_time=time(7, 0),
        woke_up_during_night=True
    )
    assert "Sleep Time" in str(log)
    assert log.woke_up_during_night is True
    assert log.wake_up_time == time(7, 0)


def test_meetings_str(user):
    meeting = Meetings.objects.create(
        user=user,
        date=date.today(),
        time=time(14, 0),
        met_people=True,
        positivity_rating=4,
        meeting_type="friends"
    )
    assert meeting.positivity_rating == 4
    assert meeting.meeting_type == "friends"
    assert "Meeting on" in str(meeting)


def test_seizure_log_str(user):
    seizure = SeizureLog.objects.create(
        user=user,
        date=date.today(),
        time=time(16, 0),
        duration_minutes=5
    )
    assert seizure.duration_minutes == 5
    assert "Seizure at" in str(seizure)
