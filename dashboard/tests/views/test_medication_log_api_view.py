import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from datetime import date


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")


@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
@patch("dashboard.views.get_user_medications_and_logs")
def test_medication_log_get(client, user, mock_get_logs):
    mock_get_logs.return_value = (["med1", "med2"], ["log1", "log2"])
    url = reverse("dashboard:medication_log")  # replace with actual name

    response = client.get(url, {"date": "2025-07-07"})
    assert response.status_code == 200
    assert "medications" in response.context
    assert "medication_logs" in response.context
    assert response.context["selected_date"] == "2025-07-07"
    assert "dashboard/log_medication.html" in [t.name for t in response.templates]


@pytest.mark.django_db
@patch("dashboard.views.save_medication_log")
@patch("dashboard.views.MedicationLogSerializer")
def test_medication_log_post_valid(client, user, mock_serializer_class, mock_save):
    url = reverse("dashboard:medication_log")

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.is_valid.return_value = True
    mock_serializer.validated_data = {"medication": "some_data"}

    response = client.post(url, {"date": "2025-07-07", "medication": 1})

    # Check redirect
    assert response.status_code == 302
    assert reverse("dashboard:dashboard_home") in response.url
    assert "date=2025-07-07" in response.url

    # Check save called
    mock_save.assert_called_once_with(user, "2025-07-07", {"medication": "some_data"})


@pytest.mark.django_db
@patch("dashboard.views.MedicationLogSerializer")
def test_medication_log_post_invalid(client, user, mock_serializer_class):
    url = reverse("dashboard:medication_log")

    mock_serializer = mock_serializer_class.return_value
    mock_serializer.is_valid.return_value = False
    mock_serializer.errors = {"medication": ["This field is required."]}

    response = client.post(url, {"date": "2025-07-07"})

    assert response.status_code == 400
    assert "medication" in response.data
