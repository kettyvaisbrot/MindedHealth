import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from datetime import date


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")


@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@patch("dashboard.views.get_meetings_by_date")
@patch("dashboard.views.MeetingsSerializer")
@pytest.mark.django_db
def test_get_meetings_found(mock_serializer_class, mock_get_meetings, client):
    mock_qs = MagicMock()
    mock_qs.exists.return_value = True
    mock_get_meetings.return_value = mock_qs

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.data = [{"dummy": "meeting"}]

    response = client.get(f"/dashboard/meetings/{date.today()}/")

    assert response.status_code == 200
    assert response.data == [{"dummy": "meeting"}]


@patch("dashboard.views.get_meetings_by_date")
@pytest.mark.django_db
def test_get_meetings_not_found(mock_get_meetings, client):
    mock_qs = MagicMock()
    mock_qs.exists.return_value = False
    mock_get_meetings.return_value = mock_qs

    response = client.get(f"/dashboard/meetings/{date.today()}/")

    assert response.status_code == 404
    assert response.data["message"] == "No meetings log for this date"


@patch("dashboard.views.create_or_update_meeting")
@patch("dashboard.views.MeetingsSerializer")
@pytest.mark.django_db
def test_post_meeting_valid(mock_serializer_class, mock_create_meeting, client):
    url = "/dashboard/meetings/"

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.is_valid.return_value = True
    mock_serializer.validated_data = {"date": str(date.today())}

    response = client.post(url, {"date": str(date.today())})

    assert response.status_code == 302
    assert "dashboard_home" in response.url
    mock_create_meeting.assert_called_once()


@patch("dashboard.views.get_meeting_or_404")
@patch("dashboard.views.MeetingsSerializer")
@pytest.mark.django_db
def test_put_meeting_valid(mock_serializer_class, mock_get_meeting, client):
    meeting_instance = MagicMock()
    mock_get_meeting.return_value = meeting_instance

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.is_valid.return_value = True

    url = f"/dashboard/meetings/{1}/"
    response = client.put(url, {"date": str(date.today())}, format="json")

    assert response.status_code == 200
    assert response.data["message"] == "Meeting updated successfully"


@patch("dashboard.views.get_meeting_or_404")
@patch("dashboard.views.delete_meeting")
@pytest.mark.django_db
def test_delete_meeting(mock_delete, mock_get_meeting, client):
    mock_meeting = MagicMock()
    mock_get_meeting.return_value = mock_meeting

    url = f"/dashboard/meetings/{1}/"
    response = client.delete(url)

    assert response.status_code == 200
    assert response.data["message"] == "Meeting deleted successfully"
    mock_delete.assert_called_once_with(mock_meeting)
