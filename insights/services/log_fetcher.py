from datetime import timedelta
from django.utils import timezone
from dashboard.models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog
from medications.models import MedicationLog

def fetch_user_logs(user):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    logs = {
        "food": FoodLog.objects.filter(user=user, date__range=(week_ago, today)),
        "sport": SportLog.objects.filter(user=user, date__range=(week_ago, today)),
        "sleep": SleepingLog.objects.filter(user=user, date__range=(week_ago, today)),
        "meetings": Meetings.objects.filter(user=user, date__range=(week_ago, today)),
        "seizures": SeizureLog.objects.filter(user=user, date__range=(week_ago, today)),
        "medications": MedicationLog.objects.filter(user=user, date__range=(week_ago, today)).select_related("medication"),
    }

    return logs
