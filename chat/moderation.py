import re

from django.conf import settings


def contains_profanity(message: str) -> bool:
    words = settings.CHAT_PROFANITY_WORDS
    if not words:
        return False
    pattern = re.compile("|".join(re.escape(w) for w in words), re.IGNORECASE)
    return bool(pattern.search(message))
