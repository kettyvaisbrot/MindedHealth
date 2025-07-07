import pytest
from dashboard.models import SleepingLog
from dashboard.services.sleeping_service import (
    get_sleeping_logs,
    get_sleeping_log_or_404,
    create_or_update_sleeping_log,
    update_sleeping_log,
    delete_sleeping_log,
)
from rest_framework.exceptions import NotFound
from django.contrib.auth.models import User
from datetime import date, time


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")


@pytest.fixture
def sleeping_log(user):
    return SleepingLog.objects.create(
        user=user,
        date=date.today(),
        went_to_sleep_yesterday=time(22, 0),
        wake_up_time=time(6, 30),
        woke_up_during_night=True,
    )


@pytest.mark.django_db
def test_get_sleeping_logs_returns_correct_logs(user):
    log = SleepingLog.objects.create(user=user, date=date.today())
    other_user = User.objects.create_user(username="other", password="pass456")
    SleepingLog.objects.create(user=other_user, date=date.today())

    logs = get_sleeping_logs(user, date.today())
    assert logs.count() == 1
    assert logs.first() == log


@pytest.mark.django_db
def test_get_sleeping_log_or_404_returns_log(user, sleeping_log):
    result = get_sleeping_log_or_404(user, date.today())
    assert result == sleeping_log


@pytest.mark.django_db
def test_get_sleeping_log_or_404_raises_if_not_found(user):
    with pytest.raises(NotFound):
        get_sleeping_log_or_404(user, date.today())


@pytest.mark.django_db
def test_create_or_update_sleeping_log_creates_new(user):
    data = {
        "date": date.today(),
        "went_to_sleep_yesterday": time(23, 0),
        "wake_up_time": time(7, 0),
        "woke_up_during_night": False,
    }
    create_or_update_sleeping_log(user, data)
    log = SleepingLog.objects.get(user=user, date=date.today())
    assert log.went_to_sleep_yesterday == time(23, 0)
    assert log.wake_up_time == time(7, 0)
    assert log.woke_up_during_night is False


@pytest.mark.django_db
def test_create_or_update_sleeping_log_updates_existing(user, sleeping_log):
    data = {
        "date": date.today(),
        "woke_up_during_night": False,
    }
    create_or_update_sleeping_log(user, data)
    sleeping_log.refresh_from_db()
    assert sleeping_log.woke_up_during_night is False


@pytest.mark.django_db
def test_update_sleeping_log_modifies_fields(sleeping_log):
    data = {"woke_up_during_night": False, "wake_up_time": time(6, 45)}
    updated = update_sleeping_log(sleeping_log, data)

    assert updated.woke_up_during_night is False
    assert updated.wake_up_time == time(6, 45)


@pytest.mark.django_db
def test_delete_sleeping_log_deletes(sleeping_log):
    delete_sleeping_log(sleeping_log)
    assert SleepingLog.objects.count() == 0
