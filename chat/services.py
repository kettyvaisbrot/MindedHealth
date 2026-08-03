import random
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import PseudonymAssignment

CHAT_TIMEZONE = ZoneInfo("Asia/Jerusalem")

# Word lists chosen to be pleasant and non-identifying -- no names, no words
# that could read as a description of a person.
_ADJECTIVES = [
    "Calm", "Quiet", "Gentle", "Bright", "Steady", "Kind", "Warm", "Brave",
    "Soft", "Clear", "Patient", "Hopeful", "Sunny", "Curious", "Mellow",
]
_ANIMALS = [
    "Fox", "Owl", "Deer", "Otter", "Falcon", "Hare", "Heron", "Lynx",
    "Robin", "Wren", "Badger", "Swan", "Finch", "Seal", "Crane",
]

_MAX_GENERATION_ATTEMPTS = 10

# The one chat room each role may access. Roles not listed here (e.g. therapist)
# have no chat access at all. Single source of truth -- both the HTTP view and
# the WebSocket consumer resolve room access through this, so they can't drift.
ROOM_NAME_BY_ROLE = {
    "patient": "patient",
    "family": "family",
}


def get_room_name_for_user(user):
    """The single room this user's role may access, or None if their role has no chat access."""
    return ROOM_NAME_BY_ROLE.get(user.role)


def get_chat_day(now=None):
    """The chat day boundary is midnight Asia/Jerusalem, not UTC or server-local time."""
    now = now or timezone.now()
    return now.astimezone(CHAT_TIMEZONE).date()


def _generate_candidate():
    adjective = random.choice(_ADJECTIVES)
    animal = random.choice(_ANIMALS)
    number = random.randint(10, 99)
    return f"{adjective} {animal} {number}"


def get_or_create_pseudonym(user, room_name):
    """
    Returns the stable pseudonym for (user, room_name, today's chat day),
    creating one if this is the user's first connection to this room today.
    """
    chat_day = get_chat_day()

    existing = PseudonymAssignment.objects.filter(
        user=user, room_name=room_name, chat_day=chat_day
    ).first()
    if existing:
        return existing.pseudonym

    for _ in range(_MAX_GENERATION_ATTEMPTS):
        try:
            with transaction.atomic():
                assignment = PseudonymAssignment.objects.create(
                    user=user,
                    room_name=room_name,
                    chat_day=chat_day,
                    pseudonym=_generate_candidate(),
                )
            return assignment.pseudonym
        except IntegrityError:
            # Either the (room, day, pseudonym) triplet collided with someone
            # else's pseudonym, or a concurrent connection from this same user
            # already created their assignment -- check for the latter before
            # retrying generation.
            existing = PseudonymAssignment.objects.filter(
                user=user, room_name=room_name, chat_day=chat_day
            ).first()
            if existing:
                return existing.pseudonym

    raise RuntimeError(
        f"Could not generate a unique pseudonym for room '{room_name}' "
        f"after {_MAX_GENERATION_ATTEMPTS} attempts"
    )
