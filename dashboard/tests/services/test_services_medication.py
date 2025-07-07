import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from medications.models import Medication, MedicationLog
from dashboard.services.medication_service import log_medication_entry
from django.shortcuts import get_object_or_404
from datetime import date
from django.core.exceptions import ObjectDoesNotExist

@pytest.mark.django_db
def test_log_medication_entry_creates_log(user):
    user = User.objects.create_user(username="tester", password="pass")
    medication = Medication.objects.create(user=user, name="Med A")
    test_date = date.today()

    log_medication_entry(user, medication.id, test_date, "12:34")

    log = MedicationLog.objects.filter(user=user, medication=medication, date=test_date).first()
    assert log is not None
    assert log.time_taken.strftime("%H:%M") == "12:34"
    assert log.dose_index == 0

@pytest.mark.django_db
def test_log_medication_entry_increments_dose_index(user):
    user = User.objects.create_user(username="tester", password="pass")
    medication = Medication.objects.create(user=user, name="Med A")
    test_date = date.today()

    # Create an existing log with dose_index=0
    MedicationLog.objects.create(user=user, medication=medication, date=test_date, time_taken="10:00", dose_index=0)

    # Now the next log should have dose_index=1
    log_medication_entry(user, medication.id, test_date, "11:00")

    logs = MedicationLog.objects.filter(user=user, medication=medication, date=test_date)
    assert logs.count() == 2
    indexes = logs.values_list("dose_index", flat=True)
    assert 1 in indexes

def test_log_medication_entry_invalid_time(user):
    user = User.objects.create_user(username="tester", password="pass")
    medication = Medication.objects.create(user=user, name="Med A")
    test_date = date.today()

    with pytest.raises(ValueError, match="Time must be in HH:MM format."):
        log_medication_entry(user, medication.id, test_date, "invalid-time")

@patch("dashboard.services.medication_service.get_object_or_404")
def test_log_medication_entry_medication_not_found(mock_get_obj, user):
    user = User.objects.create_user(username="tester", password="pass")
    test_date = date.today()
    mock_get_obj.side_effect = Exception("Not Found")

    with pytest.raises(Exception, match="Not Found"):
        log_medication_entry(user, 999, test_date, "10:00")
