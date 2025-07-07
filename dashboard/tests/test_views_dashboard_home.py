import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.utils import timezone
from unittest.mock import patch


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="pass123")


@pytest.mark.django_db
def test_dashboard_home_no_date(client, user):
    client.force_login(user)
    url = reverse("dashboard:home")  # Replace with actual name in urls.py
    response = client.get(url)

    assert response.status_code == 200
    assert "dashboard/dashboard.html" in [t.name for t in response.templates]
    messages = list(get_messages(response.wsgi_request))
    assert any("Date is required" in m.message for m in messages)


@pytest.mark.django_db
@patch("dashboard.views.parse_date_from_str")
def test_dashboard_home_invalid_date(mock_parse_date, client, user):
    client.force_login(user)
    mock_parse_date.return_value = None
    url = reverse("dashboard:home")
    response = client.get(url, {"date": "not-a-date"})

    assert response.status_code == 200
    messages = list(get_messages(response.wsgi_request))
    assert any("Invalid date format" in m.message for m in messages)


@pytest.mark.django_db
@patch("dashboard.views.fetch_dashboard_logs")
@patch("dashboard.views.parse_date_from_str")
def test_dashboard_home_valid_date(mock_parse_date, mock_fetch_logs, client, user):
    client.force_login(user)
    url = reverse("dashboard:home")

    test_date = timezone.now().date()
    mock_parse_date.return_value = test_date
    mock_fetch_logs.return_value = {
        "food_logs": [],
        "sport_logs": [],
        "sleep_logs": [],
        "meeting_logs": [],
        "seizure_logs": [],
    }

    response = client.get(url, {"date": test_date.strftime("%Y-%m-%d")})

    assert response.status_code == 200
    context = response.context

    assert context["date"] == test_date
    assert context["is_current_date"] is True
    assert "sport_choices" in context
    assert "meeting_type_choices" in context
    assert "dashboard/dashboard.html" in [t.name for t in response.templates]
