import re
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from chat.models import ModerationLog, MuteBan

MUTE_VIOLATION_THRESHOLD = 3
MUTE_LOOKBACK_HOURS = 24
MUTE_DURATION_HOURS = 24


def contains_profanity(message: str) -> bool:
    words = settings.CHAT_PROFANITY_WORDS
    if not words:
        return False
    pattern = re.compile("|".join(re.escape(w) for w in words), re.IGNORECASE)
    return bool(pattern.search(message))


# PII scope: Israeli ID number, email, phone only (Decision 9 in the planning
# doc). Free-text names/addresses are explicitly out of scope -- no reliable
# regex exists for those.
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_PATTERN = re.compile(r"(?:\+972[-\s]?|0)(?:5\d|[23489])[-\s]?\d{3}[-\s]?\d{4}\b")
_ID_CANDIDATE_PATTERN = re.compile(r"\b\d{9}\b")


def _is_valid_israeli_id(id_number: str) -> bool:
    """Official Israeli Teudat Zehut check-digit algorithm. Used so we don't
    flag every random 9-digit number (e.g. part of a phone number or a
    timestamp) as a national ID."""
    total = 0
    for i, digit in enumerate(id_number):
        num = int(digit) * (1 if i % 2 == 0 else 2)
        if num > 9:
            num -= 9
        total += num
    return total % 10 == 0


def contains_pii(message: str) -> bool:
    if _EMAIL_PATTERN.search(message):
        return True
    if _PHONE_PATTERN.search(message):
        return True
    for candidate in _ID_CANDIDATE_PATTERN.findall(message):
        if _is_valid_israeli_id(candidate):
            return True
    return False


def is_muted(user):
    """Returns muted_until if the user is currently muted, else None."""
    try:
        mute = MuteBan.objects.get(user=user)
    except MuteBan.DoesNotExist:
        return None
    if mute.muted_until and mute.muted_until > timezone.now():
        return mute.muted_until
    return None


def record_violation(user, room_name, category):
    """Logs a moderation violation and mutes the user if this is their 3rd
    violation within the trailing 24 hours. Returns muted_until if a mute
    was just applied, else None."""
    ModerationLog.objects.create(user=user, room_name=room_name, category=category)

    window_start = timezone.now() - timedelta(hours=MUTE_LOOKBACK_HOURS)
    violation_count = ModerationLog.objects.filter(
        user=user, created_at__gte=window_start
    ).count()

    if violation_count >= MUTE_VIOLATION_THRESHOLD:
        muted_until = timezone.now() + timedelta(hours=MUTE_DURATION_HOURS)
        MuteBan.objects.update_or_create(
            user=user, defaults={"muted_until": muted_until}
        )
        return muted_until

    return None
