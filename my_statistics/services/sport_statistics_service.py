from datetime import timedelta
from django.db.models import ExpressionWrapper, F, IntegerField, Avg, Count
from dashboard.models import SportLog

def fetch_sport_statistics(user, year, month):
    sport_logs = _get_annotated_sport_logs(user, year, month)
    sport_count = sport_logs.count()

    if sport_count == 0:
        return {
            "avg_sport_time": None,
            "sport_count": 0,
            "most_common_sport_activity": None,
        }

    avg_sport_time = _calculate_average_sport_time(sport_logs)
    most_common_sport_activity = _get_most_common_sport(sport_logs)

    return {
        "avg_sport_time": avg_sport_time,
        "sport_count": sport_count,
        "most_common_sport_activity": most_common_sport_activity,
    }

def _get_annotated_sport_logs(user, year, month):
    return SportLog.objects.filter(
        user=user, date__year=year, date__month=month, did_sport=True
    ).annotate(
        sport_seconds=ExpressionWrapper(
            F("sport_time__hour") * 3600 +
            F("sport_time__minute") * 60 +
            F("sport_time__second"),
            output_field=IntegerField()
        )
    )

def _calculate_average_sport_time(logs):
    avg_seconds = logs.aggregate(avg=Avg("sport_seconds"))["avg"]
    return str(timedelta(seconds=avg_seconds)) if avg_seconds is not None else None

def _get_most_common_sport(logs):
    result = (
        logs.values("sport_type")
        .annotate(count=Count("sport_type"))
        .order_by("-count")
        .first()
    )
    return result["sport_type"] if result else None
