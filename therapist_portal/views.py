from datetime import date

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
from .utils import get_owned_patient_or_404

LOG_CATEGORIES = [
    ('Food', FoodLog, format_food),
    ('Sport', SportLog, format_sport),
    ('Sleep', SleepingLog, format_sleep),
    ('Meetings', Meetings, format_meeting),
    ('Seizures', SeizureLog, format_seizure),
]


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
