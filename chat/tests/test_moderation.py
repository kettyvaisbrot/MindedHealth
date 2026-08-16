from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from chat.models import MuteBan
from chat.moderation import contains_pii, contains_profanity, is_muted, record_violation

User = get_user_model()


def test_detects_listed_word(settings):
    settings.CHAT_PROFANITY_WORDS = ["חרא", "מניאק"]
    assert contains_profanity("אתה חרא") is True


def test_detects_listed_word_case_insensitive(settings):
    settings.CHAT_PROFANITY_WORDS = ["shit"]
    assert contains_profanity("you SHIT") is True


def test_word_not_in_list_is_not_flagged(settings):
    settings.CHAT_PROFANITY_WORDS = ["חרא"]
    assert contains_profanity("אתה מניאק") is False


def test_clean_message_not_flagged(settings):
    settings.CHAT_PROFANITY_WORDS = ["חרא", "מניאק"]
    assert contains_profanity("היי, מה שלומך היום?") is False


def test_empty_word_list_never_flags_anything(settings):
    settings.CHAT_PROFANITY_WORDS = []
    assert contains_profanity("אתה חרא ומניאק") is False


@pytest.fixture
def moderated_user(db):
    return User.objects.create_user(username="dana", password="pass12345", role="patient")


@pytest.mark.django_db
def test_is_muted_returns_none_when_no_muteban_row(moderated_user):
    assert is_muted(moderated_user) is None


@pytest.mark.django_db
def test_is_muted_returns_none_for_expired_mute(moderated_user):
    MuteBan.objects.create(user=moderated_user, muted_until=timezone.now() - timedelta(hours=1))
    assert is_muted(moderated_user) is None


@pytest.mark.django_db
def test_is_muted_returns_muted_until_for_active_mute(moderated_user):
    muted_until = timezone.now() + timedelta(hours=1)
    MuteBan.objects.create(user=moderated_user, muted_until=muted_until)
    assert is_muted(moderated_user) == muted_until


@pytest.mark.django_db
def test_first_two_violations_do_not_mute(moderated_user):
    assert record_violation(moderated_user, "patient", "profanity") is None
    assert record_violation(moderated_user, "patient", "profanity") is None
    assert is_muted(moderated_user) is None


@pytest.mark.django_db
def test_third_violation_within_24h_mutes_for_24h(moderated_user):
    record_violation(moderated_user, "patient", "profanity")
    record_violation(moderated_user, "patient", "profanity")
    muted_until = record_violation(moderated_user, "patient", "profanity")

    assert muted_until is not None
    expected = timezone.now() + timedelta(hours=24)
    assert abs((muted_until - expected).total_seconds()) < 5
    assert is_muted(moderated_user) == muted_until


@pytest.mark.django_db
def test_violations_outside_24h_window_do_not_count(moderated_user):
    from chat.models import ModerationLog

    old = ModerationLog.objects.create(user=moderated_user, room_name="patient", category="profanity")
    ModerationLog.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(hours=25))

    record_violation(moderated_user, "patient", "profanity")
    muted_until = record_violation(moderated_user, "patient", "profanity")

    # Only 2 violations inside the 24h window (the 25h-old one doesn't count) -- not muted yet.
    assert muted_until is None
    assert is_muted(moderated_user) is None


# Valid Israeli ID per the official check-digit algorithm (verified by hand):
# digits 1,2,3,4,5,6,7,8 -> check digit 2.
VALID_ISRAELI_ID = "123456782"
INVALID_ISRAELI_ID = "123456789"  # same digits, wrong/no valid check digit


def test_detects_valid_israeli_id():
    assert contains_pii(f"תעודת הזהות שלי היא {VALID_ISRAELI_ID}") is True


def test_does_not_flag_nine_digits_with_invalid_checksum():
    # Not every 9-digit number is an ID -- could be a phone fragment, an
    # order number, etc. Only checksum-valid IDs should be flagged.
    assert contains_pii(f"המספר הוא {INVALID_ISRAELI_ID}") is False


def test_detects_email():
    assert contains_pii("אפשר לכתוב לי למייל dana.cohen@example.com") is True


def test_detects_israeli_mobile_phone():
    assert contains_pii("תתקשרו אליי ל-052-1234567") is True


def test_detects_israeli_phone_with_country_code():
    assert contains_pii("call me at +972-52-1234567") is True


def test_clean_message_has_no_pii():
    assert contains_pii("היי, מה שלומך היום?") is False
