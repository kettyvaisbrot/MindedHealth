import pytest
from dashboard.services.dashboard_service import fetch_dashboard_logs
from dashboard.models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog
from medications.models import MedicationLog, Medication
from django.contrib.auth.models import User
from datetime import date, time


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")


@pytest.fixture
def sample_data(user):
    today = date.today()

    FoodLog.objects.create(user=user, date=today)
    SportLog.objects.create(user=user, date=today, did_sport=True)
    SleepingLog.objects.create(user=user, went_to_sleep_yesterday=time(22, 0), wake_up_time=time(7, 0))
    Meetings.objects.create(user=user, date=today, time=time(14, 0), met_people=True)
    SeizureLog.objects.create(user=user, date=today, duration_minutes=5)

    med = Medication.objects.create(name="Vitamin D", dosage="1x", user=user)
    MedicationLog.objects.create(user=user, date=today, medication=med)

    return today


@pytest.mark.django_db
def test_fetch_dashboard_logs_returns_correct_data(user, sample_data):
    logs = fetch_dashboard_logs(user, sample_data)

    assert logs["food_logs"].count() == 1
    assert logs["sport_logs"].count() == 1
    assert logs["sleeping_logs"].count() == 1
    assert logs["meetings_logs"].count() == 1
    assert logs["seizure_logs"].count() == 1
    assert logs["medication_logs"].count() == 1
    assert hasattr(logs["medication_logs"][0], "medication")  # check select_related worked


@pytest.mark.django_db
def test_fetch_dashboard_logs_with_no_data_returns_empty_sets(user):
    today = date.today()
    logs = fetch_dashboard_logs(user, today)

    assert logs["food_logs"].count() == 0
    assert logs["sport_logs"].count() == 0
    assert logs["sleeping_logs"].count() == 0
    assert logs["meetings_logs"].count() == 0
    assert logs["seizure_logs"].count() == 0
    assert logs["medication_logs"].count() == 0


@pytest.mark.django_db
def test_fetch_dashboard_logs_does_not_include_other_users_data(user):
    today = date.today()

    # Create another user and their logs
    other_user = User.objects.create_user(username="hacker", password="pass123")
    FoodLog.objects.create(user=other_user, date=today)
    SportLog.objects.create(user=other_user, date=today)
    SleepingLog.objects.create(user=other_user, went_to_sleep_yesterday=time(23, 0), wake_up_time=time(6, 30))
    Meetings.objects.create(user=other_user, date=today, time=time(10, 0), met_people=True)
    SeizureLog.objects.create(user=other_user, date=today, duration_minutes=3)

    med = Medication.objects.create(name="Melatonin", dosage="1mg", user=other_user)
    MedicationLog.objects.create(user=other_user, date=today, medication=med)

    # Fetch logs for the original user
    logs = fetch_dashboard_logs(user, today)

    # Assert still all empty
    assert logs["food_logs"].count() == 0
    assert logs["sport_logs"].count() == 0
    assert logs["sleeping_logs"].count() == 0
    assert logs["meetings_logs"].count() == 0
    assert logs["seizure_logs"].count() == 0
    assert logs["medication_logs"].count() == 0
