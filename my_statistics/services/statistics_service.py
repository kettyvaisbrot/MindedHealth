# services/statistics_service.py

from datetime import timedelta,datetime
from django.db.models import ExpressionWrapper, F, IntegerField, Avg
from dashboard.models import FoodLog
from dashboard.models import Meetings
from django.db.models import Count
from dashboard.models import SeizureLog
from medications.models import MedicationLog, Medication


def calculate_avg_meal_time(user, year, month, meal_type):
    logs = (
        FoodLog.objects.filter(
            user=user,
            date__year=year,
            date__month=month,
            **{f"{meal_type}_ate": True}
        )
        .exclude(**{f"{meal_type}_time__isnull": True})
        .annotate(
            **{
                f"{meal_type}_seconds": ExpressionWrapper(
                    F(f"{meal_type}_time__hour") * 3600
                    + F(f"{meal_type}_time__minute") * 60
                    + F(f"{meal_type}_time__second"),
                    output_field=IntegerField(),
                )
            }
        )
    )

    if logs.exists():
        avg_seconds = logs.aggregate(avg=Avg(f"{meal_type}_seconds"))["avg"]
        return str(timedelta(seconds=avg_seconds))
    
    return None

def get_meeting_statistics_service(user, year, month):
    meetings = Meetings.objects.filter(
        user=user,
        date__year=year,
        date__month=month,
    )

    meetings_count = meetings.count()

    lowest_rating_meeting = meetings.order_by("positivity_rating").first()
    if lowest_rating_meeting:
        lowest_rating = lowest_rating_meeting.positivity_rating
        lowest_rating_type = lowest_rating_meeting.get_meeting_type_display()
    else:
        lowest_rating = None
        lowest_rating_type = None

    most_common_meeting = (
        meetings.values("meeting_type")
        .annotate(count=Count("meeting_type"))
        .order_by("-count")
        .first()
    )

    if most_common_meeting:
        most_common_meeting_type = most_common_meeting["meeting_type"]
        most_common_meeting_count = most_common_meeting["count"]
    else:
        most_common_meeting_type = None
        most_common_meeting_count = None

    return {
        "meetings_count": meetings_count,
        "lowest_rating": lowest_rating,
        "lowest_rating_type": lowest_rating_type,
        "most_common_meeting_type": most_common_meeting_type,
        "most_common_meeting_count": most_common_meeting_count,
    }


def compute_seizure_statistics(user, year, month):
    seizures = SeizureLog.objects.filter(
        user=user,
        date__year=year,
        date__month=month,
    )

    seizures_count = seizures.count()
    avg_seizure_time = None
    avg_seizure_duration = None

    if seizures_count > 0:
        seizures = seizures.annotate(
            seizure_seconds=ExpressionWrapper(
                F("time__hour") * 3600 + F("time__minute") * 60 + F("time__second"),
                output_field=IntegerField(),
            )
        )

        avg_time_sec = seizures.aggregate(
            avg_seizure_time=Avg("seizure_seconds")
        )["avg_seizure_time"]

        avg_seizure_time = str(timedelta(seconds=avg_time_sec)) if avg_time_sec else None

        avg_seizure_duration = seizures.aggregate(
            avg_duration=Avg("duration_minutes")
        )["avg_duration"]

    return {
        "seizures_count": seizures_count,
        "avg_seizure_time": avg_seizure_time,
        "avg_seizure_duration": avg_seizure_duration,
    }

def get_medication_statistics(user, year, month):
    first_day_of_month = datetime(year, month, 1).date()

    if year == datetime.now().year and month == datetime.now().month:
        last_day_of_month = datetime.now().date()
    else:
        next_month = month % 12 + 1
        next_month_year = year if month < 12 else year + 1
        first_day_of_next_month = datetime(next_month_year, next_month, 1).date()
        last_day_of_month = first_day_of_next_month - timedelta(days=1)

    medication_logs = MedicationLog.objects.filter(
        user=user, date__range=[first_day_of_month, last_day_of_month]
    )

    all_days_in_month = [
        first_day_of_month + timedelta(days=i)
        for i in range((last_day_of_month - first_day_of_month).days + 1)
    ]

    medications = Medication.objects.filter(user=user)
    medication_stats = []

    for medication in medications:
        logs_for_medication = medication_logs.filter(medication=medication)
        days_taken = set(logs_for_medication.values_list("date", flat=True))
        missed_days = [day for day in all_days_in_month if day not in days_taken]

        medication_stats.append(
            {
                "medication": medication.name,
                "days_missed": len(missed_days),
                "missed_days_list": missed_days,
            }
        )

    return medication_stats

