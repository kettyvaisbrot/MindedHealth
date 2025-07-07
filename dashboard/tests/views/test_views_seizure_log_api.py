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


@patch("dashboard.views.get_seizure_logs")
@patch("dashboard.views.SeizureLogSerializer")
@pytest.mark.django_db
def test_get_seizure_logs_found(mock_serializer_class, mock_get_seizure_logs, client):
    mock_qs = MagicMock()
    mock_qs.exists.return_value = True
    mock_get_seizure_logs.return_value = mock_qs

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.data = [{"dummy": "seizure_log"}]

    response = client.get(f"/dashboard/seizure_logs/{date.today()}/")

    assert response.status_code == 200
    assert response.data == [{"dummy": "seizure_log"}]


@patch("dashboard.views.get_seizure_logs")
@pytest.mark.django_db
def test_get_seizure_logs_not_found(mock_get_seizure_logs, client):
    mock_qs = MagicMock()
    mock_qs.exists.return_value = False
    mock_get_seizure_logs.return_value = mock_qs

    response = client.get(f"/dashboard/seizure_logs/{date.today()}/")

    assert response.status_code == 404
    assert response.data["message"] == "No seizure logs for this date"


@patch("dashboard.views.create_or_update_seizure_log")
@patch("dashboard.views.SeizureLogSerializer")
@pytest.mark.django_db
def test_post_seizure_log_valid(mock_serializer_class, mock_create_or_update, client):
    url = "/dashboard/seizure_logs/"

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.is_valid.return_value = True
    mock_serializer.validated_data = {"date": str(date.today())}

    response = client.post(url, {"date": str(date.today())})

    assert response.status_code == 302
    assert "dashboard_home" in response.url
    mock_create_or_update.assert_called_once()


@patch("dashboard.views.get_seizure_log_or_404")
@patch("dashboard.views.SeizureLogSerializer")
@pytest.mark.django_db
def test_put_seizure_log_valid(mock_serializer_class, mock_get_seizure_log, client):
    seizure_instance = MagicMock()
    mock_get_seizure_log.return_value = seizure_instance

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.is_valid.return_value = True

    url = f"/dashboard/seizure_logs/{1}/"
    response = client.put(url, {"date": str(date.today())}, format="json")

    assert response.status_code == 200
    assert response.data == mock_serializer.data


@patch("dashboard.views.get_seizure_log_or_404")
@patch("dashboard.views.delete_seizure_log")
@pytest.mark.django_db
def test_delete_seizure_log(mock_delete, mock_get_seizure_log, client):
    mock_seizure_log = MagicMock()
    mock_get_seizure_log.return_value = mock_seizure_log

    url = f"/dashboard/seizure_logs/{1}/"
    response = client.delete(url)

    assert response.status_code == 204
    mock_delete.assert_called_once_with(mock_seizure_log)
