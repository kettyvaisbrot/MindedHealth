from datetime import date, timedelta

from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect

from dashboard.models import (
    FoodLog,
    Meetings,
    MedicationIntakeLog,
    SeizureLog,
    SleepingLog,
    SportLog,
)
from medications.models import Medication
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


def get_seizures_in_range(user, start_date, end_date):
    """All SeizureLog rows for `user` between start_date and end_date
    (inclusive on both ends), one query. Shared by the seizure-days
    calendar (a calendar month) and the patient overview strip (a
    rolling 30-day window) — callers just pass different dates."""
    return SeizureLog.objects.filter(
        user=user, date__gte=start_date, date__lte=end_date,
    )


def get_medication_adherence(medication, start_date, end_date):
    """Adherence for one medication over [start_date, end_date], clamped to
    the days the medication has actually existed (its created_at) rather
    than the full period if it was added partway through — otherwise
    'expected' would count days the medication didn't exist yet.

    The percentage is intentionally uncapped above 100: taking more doses
    than prescribed is itself a signal worth surfacing, not a display bug
    to hide behind a ceiling.
    """
    active_start = max(start_date, medication.created_at.date())
    active_days = max((end_date - active_start).days + 1, 0)
    expected = medication.times_per_day * active_days

    taken = MedicationIntakeLog.objects.filter(
        user=medication.user,
        medication_ref_id=medication.id,
        date__gte=active_start,
        date__lte=end_date,
        time_taken__isnull=False,
    ).count()

    percentage = round(taken / expected * 100) if expected > 0 else 0

    return {'taken': taken, 'expected': expected, 'percentage': percentage}


def get_patients_with_medication_overuse(user_ids):
    """Returns {user_id: True/False} — whether ANY of that user's
    medications exceeded 100% adherence in the last 30 days.

    Two queries total, not one per patient per medication: all
    medications for every user_id in one query, all matching intake
    counts (grouped by user+medication) in a second — the same O(1)
    principle as get_last_activity_by_user. 'expected' itself is just
    date arithmetic in Python, no extra query."""
    today = date.today()
    start = today - timedelta(days=29)

    result = {uid: False for uid in user_ids}

    medications_by_user = {}
    for medication in Medication.objects.filter(user_id__in=user_ids):
        medications_by_user.setdefault(medication.user_id, []).append(medication)

    taken_rows = (
        MedicationIntakeLog.objects
        .filter(user_id__in=user_ids, date__gte=start, date__lte=today, time_taken__isnull=False)
        .values('user_id', 'medication_ref_id')
        .annotate(taken=Count('id'))
    )
    taken_map = {(row['user_id'], row['medication_ref_id']): row['taken'] for row in taken_rows}

    for uid, medications in medications_by_user.items():
        for medication in medications:
            active_start = max(start, medication.created_at.date())
            active_days = max((today - active_start).days + 1, 0)
            expected = medication.times_per_day * active_days
            taken = taken_map.get((uid, medication.id), 0)
            if expected > 0 and taken > expected:
                result[uid] = True
                break

    return result
