import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client
import datetime

@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")

@pytest.fixture
def client(user):
    client = Client()
    client.force_login(user)
    return client

@pytest.mark.django_db
@patch("dashboard.views.fetch_documentation_for_date")
def test_daily_documentation_view_today_date(mock_fetch, client):
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    response = client.get(reverse("dashboard:daily_documentation") + f"?date={today_str}")

    mock_fetch.assert_not_called()

    assert response.status_code == 200
    assert response.context["date"] == today_str
    assert response.context["editable"] is True
    assert response.context["documentation_data"] == {}

@pytest.mark.django_db
@patch("dashboard.views.fetch_documentation_for_date")
def test_daily_documentation_view_other_date(mock_fetch, client):
    other_date = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    mock_fetch.return_value = {"some": "data"}

    response = client.get(reverse("dashboard:daily_documentation") + f"?date={other_date}")

    mock_fetch.assert_called_once_with(other_date)
    assert response.status_code == 200
    assert response.context["date"] == other_date
    assert response.context["editable"] is False
    assert response.context["documentation_data"] == {"some": "data"}
