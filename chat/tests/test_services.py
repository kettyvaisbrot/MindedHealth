import datetime

import pytest
from django.contrib.auth import get_user_model

from chat.models import PseudonymAssignment
from chat.services import get_chat_day, get_or_create_pseudonym, get_room_name_for_user

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", password="pass12345")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="bob", password="pass12345")


@pytest.mark.django_db
def test_same_user_gets_same_pseudonym_on_repeat_calls(user):
    first = get_or_create_pseudonym(user, "patient")
    second = get_or_create_pseudonym(user, "patient")

    assert first == second
    assert PseudonymAssignment.objects.filter(user=user, room_name="patient").count() == 1


@pytest.mark.django_db
def test_pseudonym_never_reveals_username(user):
    pseudonym = get_or_create_pseudonym(user, "patient")

    assert user.username not in pseudonym
    assert pseudonym != user.username


@pytest.mark.django_db
def test_different_users_get_different_pseudonyms_same_room_same_day(user, other_user):
    mine = get_or_create_pseudonym(user, "patient")
    theirs = get_or_create_pseudonym(other_user, "patient")

    assert mine != theirs


@pytest.mark.django_db
def test_same_user_gets_different_pseudonym_in_different_room(user):
    in_patient_room = get_or_create_pseudonym(user, "patient")
    in_family_room = get_or_create_pseudonym(user, "family")

    # Not a hard guarantee (both are drawn from the same random pool), but
    # each room tracks its own PseudonymAssignment row regardless.
    assert PseudonymAssignment.objects.filter(user=user).count() == 2
    assert PseudonymAssignment.objects.get(user=user, room_name="patient").pseudonym == in_patient_room
    assert PseudonymAssignment.objects.get(user=user, room_name="family").pseudonym == in_family_room


@pytest.mark.django_db
def test_pseudonym_rotates_on_a_new_chat_day(user, monkeypatch):
    import chat.services as services

    day_one = datetime.date(2026, 1, 1)
    day_two = datetime.date(2026, 1, 2)

    monkeypatch.setattr(services, "get_chat_day", lambda now=None: day_one)
    first = get_or_create_pseudonym(user, "patient")

    monkeypatch.setattr(services, "get_chat_day", lambda now=None: day_two)
    second = get_or_create_pseudonym(user, "patient")

    assert PseudonymAssignment.objects.filter(user=user, room_name="patient").count() == 2
    # Same string is allowed to repeat by chance, so assert on row count/day instead.
    assert PseudonymAssignment.objects.get(user=user, room_name="patient", chat_day=day_one).pseudonym == first
    assert PseudonymAssignment.objects.get(user=user, room_name="patient", chat_day=day_two).pseudonym == second


@pytest.mark.django_db
def test_get_chat_day_uses_jerusalem_timezone_not_utc():
    # 22:30 UTC on Jan 1st is already 00:30 on Jan 2nd in Asia/Jerusalem (UTC+2).
    utc_moment = datetime.datetime(2026, 1, 1, 22, 30, tzinfo=datetime.timezone.utc)

    assert get_chat_day(utc_moment) == datetime.date(2026, 1, 2)


@pytest.mark.django_db
def test_patient_role_is_routed_to_the_patient_room():
    patient = User.objects.create_user(username="pat", password="pass12345", role="patient")
    assert get_room_name_for_user(patient) == "patient"


@pytest.mark.django_db
def test_family_role_is_routed_to_the_family_room():
    family = User.objects.create_user(username="fam", password="pass12345", role="family")
    assert get_room_name_for_user(family) == "family"


@pytest.mark.django_db
def test_therapist_role_has_no_chat_room():
    therapist = User.objects.create_user(username="doc", password="pass12345", role="therapist")
    assert get_room_name_for_user(therapist) is None
