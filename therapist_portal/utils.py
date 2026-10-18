from django.shortcuts import get_object_or_404, redirect

from users.models import PatientProfile, TherapistProfile


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
