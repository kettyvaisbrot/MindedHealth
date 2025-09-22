from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import User, TherapistProfile, FamilyMemberProfile, PatientProfile

@login_required
def therapist_dashboard(request):
    therapist_user = request.user
    try:
        therapist_profile = therapist_user.therapistprofile
    except TherapistProfile.DoesNotExist:
        return redirect('home')

    assigned_patients = therapist_profile.patients.all()

    search_result = None
    error_message = None

    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            patient_user = User.objects.get(email=email, role='patient')
            patient_profile = patient_user.patientprofile
            if patient_profile.therapist:
                error_message = f"{patient_user.username} already has a therapist."
            else:
                patient_profile.therapist = therapist_profile
                patient_profile.save()
                search_result = f"{patient_user.username} has been assigned to you."
        except User.DoesNotExist:
            error_message = "No patient found with this email."

    context = {
        'therapist': therapist_user,
        'assigned_patients': assigned_patients,
        'search_result': search_result,
        'error_message': error_message,
    }
    return render(request, 'users/therapist_dashboard.html', context)


@login_required
def family_dashboard(request, family_member_id):
    family_member = get_object_or_404(FamilyMemberProfile, id=family_member_id)
    
    if request.user != family_member.user:
        return redirect('home')
    
    patient = family_member.related_patient

    context = {
        'family_member': family_member,
        'patient': patient,
    }

    return render(request, 'users/family_dashboard.html', context)

def patient_detail(request, patient_id):
    patient = get_object_or_404(PatientProfile, id=patient_id)
    return render(request, 'users/patient_detail.html', {'patient': patient})