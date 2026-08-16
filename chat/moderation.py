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
