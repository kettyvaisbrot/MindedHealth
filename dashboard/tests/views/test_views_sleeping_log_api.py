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

@patch("dashboard.views.get_sleeping_logs")
@patch("dashboard.views.SleepingLogSerializer")
@pytest.mark.django_db
def test_get_sleeping_log_found(mock_serializer_class, mock_get_logs, client):
    mock_qs = MagicMock()
    mock_qs.exists.return_value = True
    mock_get_logs.return_value = mock_qs

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.data = [{"dummy": "data"}]

    response = client.get(f"/dashboard/sleepinglogs/{date.today()}/") 

    assert response.status_code == 200
    assert response.data == [{"dummy": "data"}]

@patch("dashboard.views.get_sleeping_logs")
@pytest.mark.django_db
def test_get_sleeping_log_not_found(mock_get_logs, client):
    mock_qs = MagicMock()
    mock_qs.exists.return_value = False
    mock_get_logs.return_value = mock_qs

    response = client.get(f"/dashboard/sleepinglogs/{date.today()}/")

    assert response.status_code == 404
    assert response.data["message"] == "No sleeping log for this date"

@patch("dashboard.views.create_or_update_sleeping_log")
@patch("dashboard.views.SleepingLogSerializer")
@pytest.mark.django_db
def test_post_sleeping_log_valid(mock_serializer_class, mock_create_log, client):
    url = "/dashboard/sleepinglogs/"

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.is_valid.return_value = True
    mock_serializer.validated_data = {"date": str(date.today())}

    response = client.post(url, {"date": str(date.today())})

    assert response.status_code == 302
    assert "dashboard_home" in response.url
    mock_create_log.assert_called_once()

@patch("dashboard.views.get_sleeping_log_or_404")
@patch("dashboard.views.SleepingLogSerializer")
@pytest.mark.django_db
def test_put_sleeping_log_valid(mock_serializer_class, mock_get_log, client):
    sleeping_log = MagicMock()
    mock_get_log.return_value = sleeping_log

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.is_valid.return_value = True
    mock_serializer.data = {"updated": True}

    url = f"/dashboard/sleepinglogs/{date.today()}/"
    response = client.put(url, {"date": str(date.today())}, format="json")

    assert response.status_code == 200
    assert response.data == {"updated": True}

@patch("dashboard.views.get_sleeping_log_or_404")
@patch("dashboard.views.delete_sleeping_log")
@pytest.mark.django_db
def test_delete_sleeping_log(mock_delete, mock_get_log, client):
    mock_instance = MagicMock()
    mock_get_log.return_value = mock_instance

    url = f"/dashboard/sleepinglogs/{date.today()}/"
    response = client.delete(url)

    assert response.status_code == 200
    assert response.data["message"] == "Sleeping log deleted successfully"
    mock_delete.assert_called_once_with(mock_instance)
