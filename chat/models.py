from django.conf import settings
from django.db import models

from .fields import EncryptedTextField


class ChatMessage(models.Model):
    """A persisted chat message. Wiped nightly, together with that day's
    PseudonymAssignment rows, by the day-boundary Celery task -- see chat/tasks.py."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    pseudonym = models.CharField(max_length=50)
    room_name = models.CharField(max_length=100)
    chat_day = models.DateField()
    content = EncryptedTextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["room_name", "created_at"]),
        ]

    def __str__(self):
        # Deliberately no content here -- message text should never end up in
        # logs/admin listings/reprs.
        return f"{self.pseudonym} in {self.room_name} @ {self.created_at}"


class PseudonymAssignment(models.Model):
    """
    Maps a real user to an auto-generated display name for one chat room on one
    chat day. Kept internally so the mapping can still be traced if ever needed
    (e.g. a safety concern raised in chat) -- it is just never sent to clients.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room_name = models.CharField(max_length=100)
    chat_day = models.DateField()
    pseudonym = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "room_name", "chat_day"],
                name="uniq_pseudonym_per_user_room_day",
            ),
            models.UniqueConstraint(
                fields=["room_name", "chat_day", "pseudonym"],
                name="uniq_pseudonym_per_room_day",
            ),
        ]

    def __str__(self):
        return f"{self.pseudonym} ({self.room_name}, {self.chat_day})"
