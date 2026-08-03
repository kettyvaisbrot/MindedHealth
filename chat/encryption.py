from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _get_fernet():
    key = settings.CHAT_MESSAGE_ENCRYPTION_KEY
    if not key:
        raise ImproperlyConfigured(
            "CHAT_MESSAGE_ENCRYPTION_KEY must be set to store chat message content."
        )
    return Fernet(key.encode("utf-8") if isinstance(key, str) else key)


def encrypt_text(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_text(token: str) -> str:
    return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
