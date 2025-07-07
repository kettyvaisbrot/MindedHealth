from unittest.mock import MagicMock
import pytest
from dashboard.serializers import (
    FoodLogSerializer,
    SportLogSerializer,
    SleepingLogSerializer,
    MeetingsSerializer,
    SeizureLogSerializer,
)
from dashboard.models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog
from django.contrib.auth.models import User
from datetime import date, time


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")

def test_foodlog_valid(user):
    data = {
        "user": user.id,
        "date": date.today(),
        "breakfast_ate": True,
        "breakfast_time": "08:00",
        "lunch_ate": False,
        "dinner_ate": True,
        "dinner_time": "19:00"
    }
    serializer = FoodLogSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()
    assert instance.breakfast_ate is True
    assert instance.user == user

def test_foodlog_invalid_missing_date(user):
    data = {
        "user": user.id,
        "breakfast_ate": True
    }
    serializer = FoodLogSerializer(data=data)
    assert not serializer.is_valid()
    assert "date" in serializer.errors

def test_sportlog_valid(user):
    data = {
        "user": user.id,
        "date": date.today(),
        "did_sport": True,
        "sport_type": "running",
        "sport_time": "10:00"
    }
    serializer = SportLogSerializer(data=data)
    assert serializer.is_valid()

def test_sportlog_invalid_choice(user):
    data = {
        "user": user.id,
        "date": date.today(),
        "did_sport": True,
        "sport_type": "invalid_sport"
    }
    serializer = SportLogSerializer(data=data)
    assert not serializer.is_valid()
    assert "sport_type" in serializer.errors

def test_sleepinglog_partial_valid():
    data = {
        "went_to_sleep_yesterday": "22:30",
        "wake_up_time": "07:30"
    }
    serializer = SleepingLogSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data["wake_up_time"].hour == 7

def test_sleepinglog_blank_fields():
    data = {}
    serializer = SleepingLogSerializer(data=data)
    assert serializer.is_valid()  


def test_meeting_valid(user):
    data = {
        "user": user.id,
        "date": date.today(),
        "time": "14:00",
        "met_people": True,
        "positivity_rating": 3,
        "meeting_type": "friends"
    }
    serializer = MeetingsSerializer(data=data)
    assert serializer.is_valid()
    instance = serializer.save()
    assert instance.meeting_type == "friends"

def test_meeting_invalid_rating(user):
    data = {
        "user": user.id,
        "date": date.today(),
        "time": "14:00",
        "met_people": True,
        "positivity_rating": 10  # invalid
    }
    serializer = MeetingsSerializer(data=data)
    assert not serializer.is_valid()
    assert "positivity_rating" in serializer.errors

def test_seizurelog_valid(user):
    data = {
        "date": date.today(),
        "time": "12:00",
        "duration_minutes": 5
    }
    context = {"request": MagicMock(user=user)}
    serializer = SeizureLogSerializer(data=data, context=context)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()
    assert instance.user == user
    assert instance.duration_minutes == 5

def test_seizurelog_missing_duration(user):
    data = {
        "date": date.today(),
        "time": "12:00"
    }
    context = {"request": MagicMock(user=user)}
    serializer = SeizureLogSerializer(data=data, context=context)
    assert not serializer.is_valid()
    assert "duration_minutes" in serializer.errors


