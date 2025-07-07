import pytest
from dashboard.models import SeizureLog
from dashboard.services.seizure_service import (
    get_seizure_logs,
    get_seizure_log_or_404,
    create_or_update_seizure_log,
    update_seizure_log,
    delete_seizure_log,
)
from rest_framework.exceptions import NotFound
from django.contrib.auth.models import User
from datetime import date, time


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")


@pytest.fixture
def seizure_log(user):
    return SeizureLog.objects.create(
        user=user,
        date=date.today(),
        time=time(10, 30),
        duration_minutes=15,
    )


@pytest.mark.django_db
def test_get_seizure_logs_returns_correct_logs(user, seizure_log):
    other_user = User.objects.create_user(username="other", password="pass456")
    SeizureLog.objects.create(user=other_user, date=date.today(), duration_minutes=5)

    logs = get_seizure_logs(user, date.today())
    assert logs.count() == 1
    assert logs.first() == seizure_log


@pytest.mark.django_db
def test_get_seizure_log_or_404_returns_log(seizure_log):
    found = get_seizure_log_or_404(seizure_log.pk)
    assert found == seizure_log


@pytest.mark.django_db
def test_get_seizure_log_or_404_raises_if_not_found():
    with pytest.raises(NotFound):
        get_seizure_log_or_404(999999)  


@pytest.mark.django_db
def test_create_or_update_seizure_log_creates_new(user):
    data = {
        "date": date.today(),
        "time": time(14, 0),
        "duration_minutes": 20,
    }
    create_or_update_seizure_log(user, data)
    log = SeizureLog.objects.get(user=user, date=date.today())
    assert log.duration_minutes == 20
    assert log.time == time(14, 0)


@pytest.mark.django_db
def test_create_or_update_seizure_log_updates_existing(seizure_log):
    data = {
        "date": seizure_log.date,
        "duration_minutes": 30,
    }
    create_or_update_seizure_log(seizure_log.user, data)
    seizure_log.refresh_from_db()
    assert seizure_log.duration_minutes == 30


@pytest.mark.django_db
def test_update_seizure_log_modifies_fields(seizure_log):
    data = {
        "duration_minutes": 45,
        "time": time(16, 30),
    }
    updated = update_seizure_log(seizure_log, data)
    assert updated.duration_minutes == 45
    assert updated.time == time(16, 30)


@pytest.mark.django_db
def test_delete_seizure_log_deletes(seizure_log):
    delete_seizure_log(seizure_log)
    assert SeizureLog.objects.count() == 0
