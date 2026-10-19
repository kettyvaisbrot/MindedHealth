from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect

from dashboard.models import (
    FoodLog,
    Meetings,
    MedicationIntakeLog,
    SeizureLog,
    SleepingLog,
    SportLog,
)
from users.models import PatientProfile, TherapistProfile

LAST_ACTIVITY_MODELS = (
    FoodLog, SportLog, SleepingLog, Meetings, SeizureLog, MedicationIntakeLog,
)


def get_owned_patient_or_404(request, patient_id):
    """Guard shared by every therapist_portal view: mirrors the auth
    pattern in users.views.patient_detail (login_required is still the
    caller's job via the decorator).

    Returns (patient, None) on success, or (None, redirect_response) when
    the user has no therapist profile or doesn't own this patient — callers
    do `patient, error = get_owned_patient_or_404(...); if error: return error`.
    """
    try:
        therapist_profile = request.user.therapistprofile
    except TherapistProfile.DoesNotExist:
        return None, redirect('home')

    patient = get_object_or_404(PatientProfile, id=patient_id)
    if patient.therapist != therapist_profile:
        return None, redirect('home')

    return patient, None


def get_last_activity_by_user(user_ids):
    """Returns {user_id: most_recent_date_or_None} — the latest date across
    all 6 log models, computed in exactly 6 queries total regardless of how
    many user_ids are passed in (one grouped Max('date') query per model,
    covering every user_id at once, not one query per user)."""
    result = {uid: None for uid in user_ids}

    for model in LAST_ACTIVITY_MODELS:
        rows = (
            model.objects.filter(user_id__in=user_ids)
            .values('user_id')
            .annotate(last_date=Max('date'))
        )
        for row in rows:
            uid, last_date = row['user_id'], row['last_date']
            if result[uid] is None or last_date > result[uid]:
                result[uid] = last_date

    return result
