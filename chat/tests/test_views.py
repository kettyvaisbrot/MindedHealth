import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
def test_patient_reaches_the_chat_room():
    patient = User.objects.create_user(username="pat", password="pass12345", role="patient")
    client = Client()
    client.force_login(patient)

    response = client.get(reverse("chat_room"))

    assert response.status_code == 200
    assert response.context["room_name"] == "patient"


@pytest.mark.django_db
def test_family_reaches_the_chat_room():
    family = User.objects.create_user(username="fam", password="pass12345", role="family")
    client = Client()
    client.force_login(family)

    response = client.get(reverse("chat_room"))

    assert response.status_code == 200
    assert response.context["room_name"] == "family"


@pytest.mark.django_db
def test_therapist_is_redirected_away_from_chat():
    therapist = User.objects.create_user(username="doc", password="pass12345", role="therapist")
    client = Client()
    client.force_login(therapist)

    response = client.get(reverse("chat_room"))

    assert response.status_code == 302
    assert response.url == reverse("home")


@pytest.mark.django_db
def test_anonymous_user_is_redirected_to_login():
    client = Client()

    response = client.get(reverse("chat_room"))

    assert response.status_code == 302
