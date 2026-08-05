import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model

from users.models import TherapistProfile, PatientProfile
from users.views import patient_detail

User = get_user_model()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
def test_assigned_therapist_can_view(rf):
    therapist_user = User.objects.create_user(username="t1", password="x", role="therapist")
    therapist_profile = TherapistProfile.objects.create(user=therapist_user, specialization="X", license_number="1")
    patient_user = User.objects.create_user(username="p1", password="x", role="patient")
    patient_profile = PatientProfile.objects.create(user=patient_user, therapist=therapist_profile)

    request = rf.get(f"/patient/{patient_profile.id}/")
    request.user = therapist_user
    response = patient_detail(request, patient_profile.id)
    assert response.status_code == 200
    assert b"p1" in response.content


@pytest.mark.django_db
def test_unassigned_therapist_is_redirected(rf):
    owner_therapist_user = User.objects.create_user(username="t_owner", password="x", role="therapist")
    owner_profile = TherapistProfile.objects.create(user=owner_therapist_user, specialization="X", license_number="1")
    other_therapist_user = User.objects.create_user(username="t_other", password="x", role="therapist")
    TherapistProfile.objects.create(user=other_therapist_user, specialization="X", license_number="2")
    patient_user = User.objects.create_user(username="p2", password="x", role="patient")
    patient_profile = PatientProfile.objects.create(user=patient_user, therapist=owner_profile)

    request = rf.get(f"/patient/{patient_profile.id}/")
    request.user = other_therapist_user
    response = patient_detail(request, patient_profile.id)
    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_non_therapist_is_redirected(rf):
    patient_user = User.objects.create_user(username="p3", password="x", role="patient")
    other_patient_user = User.objects.create_user(username="p4", password="x", role="patient")
    therapist_user = User.objects.create_user(username="t3", password="x", role="therapist")
    therapist_profile = TherapistProfile.objects.create(user=therapist_user, specialization="X", license_number="1")
    patient_profile = PatientProfile.objects.create(user=patient_user, therapist=therapist_profile)

    request = rf.get(f"/patient/{patient_profile.id}/")
    request.user = other_patient_user
    response = patient_detail(request, patient_profile.id)
    assert response.status_code == 302
    assert response.url == "/"
