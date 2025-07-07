import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client
from medications.models import MedicationLog
from datetime import date

@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")

@pytest.fixture
def client(user):
    client = Client()
    client.force_login(user)
    return client

@pytest.mark.django_db
def test_log_medication_get(client, user):
    test_date = date.today()
    MedicationLog.objects.create(user=user, date=test_date, dose_index=0, time_taken="10:00", medication_id=1)

    url = reverse("dashboard:log_medication", args=[test_date.strftime("%Y-%m-%d")])
    response = client.get(url)

    assert response.status_code == 200
    assert "logs" in response.context
    assert response.context["date"] == test_date.strftime("%Y-%m-%d")

@patch("dashboard.views.log_medication_entry")
@pytest.mark.django_db
def test_log_medication_post_success(mock_log_entry, client):
    test_date = date.today()
    url = reverse("dashboard:log_medication", args=[test_date.strftime("%Y-%m-%d")])
    data = {"time_taken": "10:30", "medication": "1"}

    response = client.post(url, data)

    mock_log_entry.assert_called_once()
    assert response.status_code == 200
    assert "success_message" in response.context
    assert response.context["success_message"] == "Medication entry saved successfully!"

@pytest.mark.django_db
def test_log_medication_post_missing_fields(client):
    test_date = date.today()
    url = reverse("dashboard:log_medication", args=[test_date.strftime("%Y-%m-%d")])
    data = {"time_taken": "", "medication": ""}

    response = client.post(url, data)

    assert response.status_code == 200
    assert "error_message" in response.context
    assert response.context["error_message"] == "Time and Medication selection are required."

@patch("dashboard.views.log_medication_entry")
@pytest.mark.django_db
def test_log_medication_post_exception(mock_log_entry, client):
    mock_log_entry.side_effect = Exception("Something went wrong")
    test_date = date.today()
    url = reverse("dashboard:log_medication", args=[test_date.strftime("%Y-%m-%d")])
    data = {"time_taken": "10:30", "medication": "1"}

    response = client.post(url, data)

    assert response.status_code == 200
    assert "error_message" in response.context
    assert "An error occurred: Something went wrong" in response.context["error_message"]
