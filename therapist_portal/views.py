import calendar
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from dashboard.models import FoodLog, Meetings, MedicationIntakeLog, SeizureLog, SleepingLog, SportLog
from medications.models import Medication
from .formatters import (
    format_food,
    format_meeting,
    format_medication,
    format_seizure,
    format_sleep,
    format_sport,
)
from .utils import get_medication_adherence, get_owned_patient_or_404, get_seizures_in_range

LOG_CATEGORIES = [
    ('Food', FoodLog, format_food),
    ('Sport', SportLog, format_sport),
    ('Sleep', SleepingLog, format_sleep),
    ('Meetings', Meetings, format_meeting),
    ('Seizures', SeizureLog, format_seizure),
]

ADHERENCE_PERIODS = (7, 30, 90)


@login_required
@require_POST
def unassign_patient(request, patient_id):
    patient, error = get_owned_patient_or_404(request, patient_id)
    if error:
        return error

    patient.therapist = None
    patient.save()
    return redirect('therapist_dashboard')


@login_required
def patient_documentation(request, patient_id):
    patient, error = get_owned_patient_or_404(request, patient_id)
    if error:
        return error

    selected_date = request.GET.get('date') or date.today().isoformat()

    categories = []
    for label, model, formatter in LOG_CATEGORIES:
        logs = model.objects.filter(user=patient.user, date=selected_date)
        if logs.exists():
            categories.append({'label': label, 'entries': [formatter(log) for log in logs]})

    med_logs = MedicationIntakeLog.objects.filter(user=patient.user, date=selected_date)
    if med_logs.exists():
        med_ids = {log.medication_ref_id for log in med_logs}
        medication_names = dict(Medication.objects.filter(id__in=med_ids).values_list('id', 'name'))
        categories.append({
            'label': 'Medications',
            'entries': [format_medication(log, medication_names) for log in med_logs],
        })

    context = {
        'patient': patient,
        'selected_date': selected_date,
        'categories': categories,
        'has_documentation': bool(categories),
    }
    return render(request, 'therapist_portal/patient_documentation.html', context)


@login_required
def patient_seizures(request, patient_id):
    patient, error = get_owned_patient_or_404(request, patient_id)
    if error:
        return error

    today = date.today()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        if not 1 <= month <= 12:
            raise ValueError
    except (TypeError, ValueError):
        year, month = today.year, today.month

    # Industry-standard soft clamp, not a hard error: a future month is a
    # nonsensical request (nothing can exist there), not a security concern
    # (get_owned_patient_or_404 above is the real auth boundary) — so we
    # silently show the current month instead of rejecting the request.
    if (year, month) > (today.year, today.month):
        year, month = today.year, today.month

    first_day = date(year, month, 1)
    days_in_month = calendar.monthrange(year, month)[1]
    last_day = date(year, month, days_in_month)

    seizures = get_seizures_in_range(patient.user, first_day, last_day)
    seizures_by_day = {}
    for seizure in seizures:
        seizures_by_day.setdefault(seizure.date.day, []).append(seizure)

    cal = calendar.Calendar(firstweekday=6)  # weeks start Sunday
    weeks = []
    for week in cal.monthdayscalendar(year, month):
        week_cells = []
        for day_number in week:
            if day_number == 0:
                week_cells.append(None)
            else:
                week_cells.append({
                    'day': day_number,
                    'count': len(seizures_by_day.get(day_number, [])),
                })
        weeks.append(week_cells)

    detail_days = [
        {'day': day_number, 'entries': [format_seizure(s) for s in seizures_by_day[day_number]]}
        for day_number in sorted(seizures_by_day)
    ]

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    context = {
        'patient': patient,
        'month_name': first_day.strftime('%B %Y'),
        'weeks': weeks,
        'detail_days': detail_days,
        'has_seizures': bool(detail_days),
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'is_current_month': (year, month) == (today.year, today.month),
    }
    return render(request, 'therapist_portal/patient_seizures.html', context)


@login_required
def patient_medications(request, patient_id):
    patient, error = get_owned_patient_or_404(request, patient_id)
    if error:
        return error

    try:
        period = int(request.GET.get('period', 30))
        if period not in ADHERENCE_PERIODS:
            raise ValueError
    except (TypeError, ValueError):
        period = 30

    end_date = date.today()
    start_date = end_date - timedelta(days=period - 1)

    medications = [
        {'name': medication.name, **get_medication_adherence(medication, start_date, end_date)}
        for medication in Medication.objects.filter(user=patient.user)
    ]

    context = {
        'patient': patient,
        'period': period,
        'periods': ADHERENCE_PERIODS,
        'medications': medications,
        'has_medications': bool(medications),
    }
    return render(request, 'therapist_portal/patient_medications.html', context)
