from dashboard.models import (
    FoodLog, SportLog, SleepingLog, Meetings,
    SeizureLog
)
from medications.models import MedicationLog
from django.utils import timezone

def fetch_dashboard_logs(user, date):
    return {
        "food_logs": FoodLog.objects.filter(user=user, date=date),
        "sport_logs": SportLog.objects.filter(user=user, date=date),
        "sleeping_logs": SleepingLog.objects.filter(user=user, date=date),
        "meetings_logs": Meetings.objects.filter(user=user, date=date),
        "seizure_logs": SeizureLog.objects.filter(user=user, date=date),
        "medication_logs": MedicationLog.objects.filter(user=user, date=date).select_related("medication"),
    }
