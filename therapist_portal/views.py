from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .utils import get_owned_patient_or_404


@login_required
@require_POST
def unassign_patient(request, patient_id):
    patient, error = get_owned_patient_or_404(request, patient_id)
    if error:
        return error

    patient.therapist = None
    patient.save()
    return redirect('therapist_dashboard')
