import pytest
from datetime import date, time
from medications.models import Medication, MedicationLog
from dashboard.services.medication_service import (
    save_medication_log,
    get_next_dose_index,
    log_medication_entry,
)
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.shortcuts import Http404


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass123")


@pytest.fixture
def medication(user):
    return Medication.objects.create(name="TestMed", dosage="1x", user=user)


@pytest.mark.django_db
def test_save_medication_log_creates_new_log(user, medication):
    validated_data = {
        "medication": medication,
        "time_taken": time(8, 30),
        "dose_index": 0,
    }
    save_medication_log(user, date.today(), validated_data)

    log = MedicationLog.objects.get(user=user, medication=medication)
    assert log.time_taken == time(8, 30)
    assert log.dose_index == 0


@pytest.mark.django_db
def test_save_medication_log_updates_existing_log(user, medication):
    MedicationLog.objects.create(
        user=user,
        medication=medication,
        date=date.today(),
        time_taken=time(7, 0),
        dose_index=0,
    )

    validated_data = {
        "medication": medication,
        "time_taken": time(10, 0),
        "dose_index": 0,
    }

    save_medication_log(user, date.today(), validated_data)

    updated_log = MedicationLog.objects.get(user=user, dose_index=0)
    assert updated_log.time_taken == time(10, 0)


@pytest.mark.django_db
def test_get_next_dose_index_returns_zero_when_none(user, medication):
    index = get_next_dose_index(user, medication, date.today())
    assert index == 0


@pytest.mark.django_db
def test_get_next_dose_index_returns_next_value(user, medication):
    MedicationLog.objects.create(
        user=user,
        medication=medication,
        date=date.today(),
        time_taken=time(8, 0),
        dose_index=1,
    )
    index = get_next_dose_index(user, medication, date.today())
    assert index == 2


@pytest.mark.django_db
def test_log_medication_entry_creates_log(user, medication):
    log_medication_entry(user, medication.id, date.today(), "09:15")

    log = MedicationLog.objects.get(user=user, medication=medication)
    assert log.time_taken == time(9, 15)
    assert log.dose_index == 0


@pytest.mark.django_db
def test_log_medication_entry_invalid_time(user, medication):
    with pytest.raises(ValueError, match="Time must be in HH:MM format."):
        log_medication_entry(user, medication.id, date.today(), "invalid-time")


@pytest.mark.django_db
def test_log_medication_entry_invalid_medication(user):
    with pytest.raises(Http404):
        log_medication_entry(user, medication_id=999, date=date.today(), time_taken_str="08:00")
