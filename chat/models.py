from django.conf import settings
from django.db import models


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
