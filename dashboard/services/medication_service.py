from medications.models import Medication, MedicationLog
from django.db.models import Max
from django.shortcuts import get_object_or_404

def get_user_medications_and_logs(user, date):
    medications = Medication.objects.filter(user=user)
    medication_logs = MedicationLog.objects.filter(user=user, date=date)
    return medications, medication_logs

def save_medication_log(user, date, validated_data):
    MedicationLog.objects.update_or_create(
        user=user,
        date=date,
        dose_index=validated_data["dose_index"],
        defaults={
            "time_taken": validated_data["time_taken"],
            "medication": validated_data["medication"],
        },
    )

def get_next_dose_index(user, medication, date):
    existing_logs = MedicationLog.objects.filter(user=user, medication=medication, date=date)
    max_dose_index = existing_logs.aggregate(max_index=Max("dose_index"))["max_index"]
    return (max_dose_index + 1) if max_dose_index is not None else 0

def log_medication_entry(user, medication_id, date, time_taken_str):
    from django.utils import timezone
    from datetime import datetime

    # Validate and parse time_taken
    try:
        time_taken = datetime.strptime(time_taken_str, "%H:%M").time()
    except ValueError:
        raise ValueError("Time must be in HH:MM format.")

    medication = get_object_or_404(Medication, id=medication_id, user=user)

    next_dose_index = get_next_dose_index(user, medication, date)

    MedicationLog.objects.create(
        user=user,
        medication=medication,
        date=date,
        time_taken=time_taken,
        dose_index=next_dose_index,
    )
