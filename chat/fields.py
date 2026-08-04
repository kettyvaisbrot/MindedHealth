from django.db import models

from .encryption import decrypt_text, encrypt_text


class EncryptedTextField(models.TextField):
    """A TextField that is encrypted at rest, transparent to code reading/writing it."""

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        return encrypt_text(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_text(value)
