import pytest
from dashboard.models import SportLog
from dashboard.services.sport_service import (
    get_sport_logs,
    get_sport_log_or_404,
    create_or_update_sport_log,
    update_sport_log,
    delete_sport_log,
)
from rest_framework.exceptions import NotFound
from django.contrib.auth.models import User
from datetime import date, time


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")


@pytest.fixture
def sport_log(user):
    return SportLog.objects.create(
        user=user,
        date=date.today(),
        did_sport=True,
        sport_type="running",
        sport_time=time(7, 30),
    )


@pytest.mark.django_db
def test_get_sport_logs_returns_correct_logs(user):
    log = SportLog.objects.create(user=user, date=date.today())
    other_user = User.objects.create_user(username="hacker", password="hack123")
    SportLog.objects.create(user=other_user, date=date.today())

    logs = get_sport_logs(user, date.today())
    assert logs.count() == 1
    assert logs.first() == log


@pytest.mark.django_db
def test_get_sport_log_or_404_returns_log(user, sport_log):
    result = get_sport_log_or_404(user, date.today())
    assert result == sport_log


@pytest.mark.django_db
def test_get_sport_log_or_404_raises_if_not_found(user):
    with pytest.raises(NotFound):
        get_sport_log_or_404(user, date.today())


@pytest.mark.django_db
def test_create_or_update_sport_log_creates_new(user):
    data = {
        "date": date.today(),
        "did_sport": True,
        "sport_type": "running",
    }
    create_or_update_sport_log(user, data)
    log = SportLog.objects.get(user=user, date=date.today())
    assert log.did_sport is True
    assert log.sport_type == "running"


@pytest.mark.django_db
def test_create_or_update_sport_log_updates_existing(user, sport_log):
    data = {
        "date": date.today(),
        "did_sport": False, 
    }
    create_or_update_sport_log(user, data)
    sport_log.refresh_from_db()
    assert sport_log.did_sport is False


@pytest.mark.django_db
def test_update_sport_log_modifies_fields(sport_log):
    data = {"did_sport": False, "sport_type": "walking"}
    updated = update_sport_log(sport_log, data)

    assert updated.did_sport is False
    assert updated.sport_type == "walking"


@pytest.mark.django_db
def test_delete_sport_log_deletes(sport_log):
    delete_sport_log(sport_log)
    assert SportLog.objects.count() == 0
