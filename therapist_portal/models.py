from django.conf import settings
from django.db import models


class PatientAlert(models.Model):
    """Placeholder for the future crisis-detection mechanism (see
    feature_chat_moderation_safety.md §7 for the planned SafetyFlag).
    No detection logic writes to this yet — it only exists so the
    therapist list's alert indicator has something to query."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    room_name = models.CharField(max_length=100)
    reason = models.CharField(max_length=50)
    therapist_notified = models.BooleanField(default=False)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
