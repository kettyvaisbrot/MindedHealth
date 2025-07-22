from .models import Medication, MedicationLog
from django.shortcuts import get_object_or_404



def delete_medication(medication):
    medication.delete()


def log_medication(user, medication, date, time_taken, dose_index):
    log = MedicationLog.objects.create(
        user=user,
        medication=medication,
        date=date,
        time_taken=time_taken,
        dose_index=dose_index,
    )
    return log

def log_medication_service(user, medication_id, date, time_taken, dose_index):
    medication = get_object_or_404(Medication, pk=medication_id, user=user)
    
    # Call your actual logging function (e.g. saving MedicationLog or similar)
    log_medication(
        user=user,
        medication=medication,
        date=date,
        time_taken=time_taken,
        dose_index=dose_index,
    )

