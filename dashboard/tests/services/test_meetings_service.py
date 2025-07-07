import pytest
from dashboard.models import Meetings
from dashboard.services.meetings_service import (
    get_meetings_by_date,
    get_meeting_or_404,
    create_or_update_meeting,
    update_meeting,
    delete_meeting,
)
from rest_framework.exceptions import NotFound
from django.contrib.auth.models import User
from datetime import date, time


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")


@pytest.fixture
def meeting(user):
    return Meetings.objects.create(
        user=user,
        date=date.today(),
        time=time(14, 30),
        met_people=True,
        positivity_rating=4,
        meeting_type="family",
    )


@pytest.mark.django_db
def test_get_meetings_by_date_returns_correct_meetings(user, meeting):
    other_user = User.objects.create_user(username="other", password="pass456")
    Meetings.objects.create(user=other_user, date=date.today())

    meetings = get_meetings_by_date(user, date.today())
    assert meetings.count() == 1
    assert meetings.first() == meeting


@pytest.mark.django_db
def test_get_meeting_or_404_returns_meeting(meeting):
    found = get_meeting_or_404(meeting.pk)
    assert found == meeting


@pytest.mark.django_db
def test_get_meeting_or_404_raises_if_not_found():
    with pytest.raises(NotFound):
        get_meeting_or_404(999999)


@pytest.mark.django_db
def test_create_or_update_meeting_creates_new(user):
    data = {
        "date": date.today(),
        "time": time(15, 0),
        "met_people": False,
        "positivity_rating": 3,
        "meeting_type": "friends",
    }
    create_or_update_meeting(user, data)
    meeting = Meetings.objects.get(user=user, date=date.today())
    assert meeting.met_people is False
    assert meeting.meeting_type == "friends"


@pytest.mark.django_db
def test_create_or_update_meeting_updates_existing(meeting):
    data = {
        "date": meeting.date,
        "met_people": False,
        "positivity_rating": 1,
    }
    create_or_update_meeting(meeting.user, data)
    meeting.refresh_from_db()
    assert meeting.met_people is False
    assert meeting.positivity_rating == 1


@pytest.mark.django_db
def test_update_meeting_modifies_fields(meeting):
    data = {
        "positivity_rating": 5,
        "meeting_type": "business",
    }
    updated = update_meeting(meeting, data)
    assert updated.positivity_rating == 5
    assert updated.meeting_type == "business"


@pytest.mark.django_db
def test_delete_meeting_deletes(meeting):
    delete_meeting(meeting)
    assert Meetings.objects.count() == 0
