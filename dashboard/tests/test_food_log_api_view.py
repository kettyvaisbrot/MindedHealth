import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from datetime import date


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")


@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@patch("dashboard.views.get_food_logs")
@patch("dashboard.views.FoodLogSerializer")
@pytest.mark.django_db
def test_food_log_get_found(mock_serializer_class, mock_get_logs, client, user):
    mock_qs = MagicMock()
    mock_qs.exists.return_value = True
    mock_get_logs.return_value = mock_qs

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.data = [{"dummy": "data"}]

    response = client.get(f"/dashboard/foodlogs/{date.today()}/")  # Adjust path to match your router

    assert response.status_code == 200
    assert response.data == [{"dummy": "data"}]


@patch("dashboard.views.get_food_logs")
@pytest.mark.django_db
def test_food_log_get_not_found(mock_get_logs, client):
    mock_qs = MagicMock()
    mock_qs.exists.return_value = False
    mock_get_logs.return_value = mock_qs

    response = client.get(f"/dashboard/foodlogs/{date.today()}/")

    assert response.status_code == 404
    assert response.data["message"] == "No food log for this date"


@patch("dashboard.views.create_or_update_food_log")
@patch("dashboard.views.FoodLogSerializer")
@pytest.mark.django_db
def test_food_log_post_valid(mock_serializer_class, mock_create_log, client, user):
    url = "/dashboard/foodlogs/"  # Adjust to your actual route

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.is_valid.return_value = True
    mock_serializer.validated_data = {
        "date": str(date.today()),
        "breakfast_ate": True,
    }

    response = client.post(url, {"date": str(date.today()), "breakfast_ate": True})

    assert response.status_code == 302
    assert "dashboard_home" in response.url
    mock_create_log.assert_called_once()


@patch("dashboard.views.get_food_log_or_404")
@patch("dashboard.views.FoodLogSerializer")
@pytest.mark.django_db
def test_food_log_put_valid(mock_serializer_class, mock_get_log, client, user):
    food_log = MagicMock()
    mock_get_log.return_value = food_log

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.is_valid.return_value = True
    mock_serializer.data = {"updated": True}

    url = f"/dashboard/foodlogs/{date.today()}/"
    response = client.put(url, {"date": str(date.today()), "breakfast_ate": False}, format="json")

    assert response.status_code == 200
    assert response.data == {"updated": True}


@patch("dashboard.views.get_food_log_or_404")
@patch("dashboard.views.delete_food_log")
@pytest.mark.django_db
def test_food_log_delete(mock_delete, mock_get_log, client):
    mock_instance = MagicMock()
    mock_get_log.return_value = mock_instance

    url = f"/dashboard/foodlogs/{date.today()}/"
    response = client.delete(url)

    assert response.status_code == 200
    assert response.data["message"] == "Food log deleted successfully"
    mock_delete.assert_called_once_with(mock_instance)

