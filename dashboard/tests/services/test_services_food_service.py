import pytest
from dashboard.models import FoodLog
from dashboard.services.food_service import (
    get_food_logs,
    get_food_log_or_404,
    create_or_update_food_log,
    update_food_log,
    delete_food_log,
)
from rest_framework.exceptions import NotFound
from django.contrib.auth.models import User
from datetime import date, time


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")

@pytest.fixture
def food_log(user):
    return FoodLog.objects.create(
        user=user,
        date=date.today(),
        breakfast_ate=True,
        lunch_ate=False,
        dinner_ate=True,
        breakfast_time=time(8, 0),
        dinner_time=time(19, 30),
    )

@pytest.mark.django_db
def test_get_food_logs_returns_correct_logs(user):
    log = FoodLog.objects.create(user=user, date=date.today())
    other_user = User.objects.create_user(username="hacker", password="hack123")
    FoodLog.objects.create(user=other_user, date=date.today())

    logs = get_food_logs(user, date.today())
    assert logs.count() == 1
    assert logs.first() == log

@pytest.mark.django_db
def test_get_food_log_or_404_returns_log(user, food_log):
    result = get_food_log_or_404(user, date.today())
    assert result == food_log

@pytest.mark.django_db
def test_get_food_log_or_404_raises_if_not_found(user):
    with pytest.raises(NotFound):
        get_food_log_or_404(user, date.today())

@pytest.mark.django_db
def test_create_or_update_food_log_creates_new(user):
    data = {
        "date": date.today(),
        "breakfast_ate": True,
        "lunch_ate": False,
        "dinner_ate": True,
    }
    create_or_update_food_log(user, data)
    log = FoodLog.objects.get(user=user, date=date.today())
    assert log.breakfast_ate is True
    assert log.lunch_ate is False

@pytest.mark.django_db
def test_create_or_update_food_log_updates_existing(user, food_log):
    data = {
        "date": date.today(),
        "breakfast_ate": False,
    }
    create_or_update_food_log(user, data)
    food_log.refresh_from_db()
    assert food_log.breakfast_ate is False


@pytest.mark.django_db
def test_update_food_log_modifies_fields(food_log):
    data = {"lunch_ate": True, "breakfast_ate": False}
    updated = update_food_log(food_log, data)

    assert updated.lunch_ate is True
    assert updated.breakfast_ate is False

@pytest.mark.django_db
def test_delete_food_log_deletes(food_log):
    delete_food_log(food_log)
    assert FoodLog.objects.count() == 0

