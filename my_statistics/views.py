from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, F, ExpressionWrapper, IntegerField, Count
from datetime import datetime, timedelta
from calendar import month_name
from dashboard.models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog
import calendar
from medications.models import Medication, MedicationLog
from django.http import JsonResponse
from django.db.models import Count


def keep_alive(request):
    # Simply return a success response to reset the session timer
    return JsonResponse({"status": "success"})


@login_required
def statistics_view(request):
    selected_month = request.GET.get("month", None)
    selected_year = request.GET.get("year", None)

    if not selected_month or not selected_year:
        current_date = datetime.now().date()
        selected_month = current_date.month
        selected_year = current_date.year

    selected_month = int(selected_month)
    selected_year = int(selected_year)

    # Generating month choices for the dropdown
    month_choices = [(month_num, month_name[month_num]) for month_num in range(1, 13)]

    # Retrieve statistics based on selected month and year
    breakfast_stats = get_avg_meal_time(
        request.user, selected_year, selected_month, "breakfast"
    )
    lunch_stats = get_avg_meal_time(
        request.user, selected_year, selected_month, "lunch"
    )
    dinner_stats = get_avg_meal_time(
        request.user, selected_year, selected_month, "dinner"
    )
    sport_stats = get_sport_statistics(request.user, selected_year, selected_month)
    sleep_stats = get_sleeping_statistics(request.user, selected_year, selected_month)
    meeting_stats = get_meeting_statistics(request.user, selected_year, selected_month)
    seizure_stats = get_seizure_statistics(request.user, selected_year, selected_month)
    seizure_stats_with_events = get_seizure_statistics_with_previous_event(
        request.user, selected_year, selected_month
    )
    seizure_statistics = get_seizure_statistics_with_previous_event(
        request.user, selected_year, selected_month
    )
    medication_statistics = get_medication_statistics(
        request.user, selected_month, selected_year
    )

    # Get the number of days in the specified month
    days_in_month = calendar.monthrange(selected_year, selected_month)[1]

    # Create a dictionary to hold sleep durations
    sleep_durations = {}

    # Loop through each day in the specified month
    for day in range(1, days_in_month + 1):
        current_date = datetime(selected_year, selected_month, day).date()

        # Fetch the sleep log for the current date only
        sleep_log = SleepingLog.objects.filter(date=current_date).first()

        if sleep_log and sleep_log.went_to_sleep_yesterday and sleep_log.wake_up_time:
            sleep_time = datetime.combine(
                current_date, sleep_log.went_to_sleep_yesterday
            )
            wake_up_time = datetime.combine(current_date, sleep_log.wake_up_time)

            # If wake_up_time is earlier or equal, add one day
            if wake_up_time <= sleep_time:
                wake_up_time += timedelta(days=1)

            duration = wake_up_time - sleep_time

            days = duration.days
            hours = duration.seconds // 3600
            minutes = (duration.seconds // 60) % 60

            sleep_durations[current_date] = {
                "days": days,
                "hours": hours,
                "minutes": minutes,
            }

    context = {
        "breakfast_stats": breakfast_stats,
        "lunch_stats": lunch_stats,
        "dinner_stats": dinner_stats,
        "sport_stats": sport_stats,
        "sleep_stats": sleep_stats,
        "meeting_stats": meeting_stats,
        "seizure_stats": seizure_stats,
        "seizure_statistics": seizure_statistics,
        "current_month": selected_month,
        "current_year": selected_year,
        "month_choices": month_choices,
        "seizure_stats_with_events": seizure_stats_with_events,
        "sleep_durations": sleep_durations,
        "medication_statistics": medication_statistics,
    }

    return render(request, "my_statistics/statistics.html", context)


def get_avg_meal_time(user, year, month, meal_type):
    """Helper function to calculate average meal time for a given user, year, month, and meal type."""
    meal_logs = (
        FoodLog.objects.filter(
            user=user, date__year=year, date__month=month, **{f"{meal_type}_ate": True}
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

    if meal_logs.exists():
        avg_time_seconds = meal_logs.aggregate(avg_time=Avg(f"{meal_type}_seconds"))[
            "avg_time"
        ]
        avg_time = str(timedelta(seconds=avg_time_seconds))
    else:
        avg_time = None

    return avg_time


def get_sport_statistics(user, year, month):
    """Helper function to retrieve sport statistics for a given user, year, and month."""
    sport_logs = SportLog.objects.filter(
        user=user, date__year=year, date__month=month, did_sport=True
    ).annotate(
        sport_seconds=ExpressionWrapper(
            F("sport_time__hour") * 3600
            + F("sport_time__minute") * 60
            + F("sport_time__second"),
            output_field=IntegerField(),
        )
    )

    sport_count = sport_logs.count()

    if sport_count > 0:
        avg_sport_time_seconds = sport_logs.aggregate(
            avg_sport_time=Avg("sport_seconds")
        )["avg_sport_time"]
        avg_sport_time = str(timedelta(seconds=avg_sport_time_seconds))

        most_common_sport = (
            sport_logs.values("sport_type")
            .annotate(count=Count("sport_type"))
            .order_by("-count")
            .first()
        )
        if most_common_sport:
            most_common_sport_activity = most_common_sport["sport_type"]
        else:
            most_common_sport_activity = None
    else:
        avg_sport_time = None
        most_common_sport_activity = None

    return {
        "avg_sport_time": avg_sport_time,
        "sport_count": sport_count,
        "most_common_sport_activity": most_common_sport_activity,
    }


def convert_seconds_to_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return hours, minutes


def get_sleeping_statistics(user, year, month):
    """Helper function to calculate sleeping statistics for a given user, year, and month."""
    sleeping_logs = SleepingLog.objects.filter(
        user=user,
        date__year=year,
        date__month=month,
    )

    days_count = sleeping_logs.count()

    if days_count > 0:
        avg_wake_time, avg_sleep_time = calculate_avg_sleep_times(sleeping_logs)
        nights_awake_count = sleeping_logs.filter(woke_up_during_night=True).count()
    else:
        avg_wake_time = None
        avg_sleep_time = None
        nights_awake_count = None

    return {
        "avg_wake_time": avg_wake_time,
        "avg_sleep_time": avg_sleep_time,
        "nights_awake_count": nights_awake_count,
        "days_count": days_count,
    }


def calculate_avg_sleep_times(sleeping_logs):
    total_wake_seconds = 0
    total_sleep_seconds = 0
    count = 0

    for log in sleeping_logs:
        if log.wake_up_time and log.went_to_sleep_yesterday:
            wake_seconds = (
                log.wake_up_time.hour * 3600
                + log.wake_up_time.minute * 60
                + log.wake_up_time.second
            )
            sleep_seconds = (
                log.went_to_sleep_yesterday.hour * 3600
                + log.went_to_sleep_yesterday.minute * 60
                + log.went_to_sleep_yesterday.second
            )

            total_wake_seconds += wake_seconds
            total_sleep_seconds += sleep_seconds
            count += 1

    if count > 0:
        avg_wake_seconds = total_wake_seconds / count
        avg_sleep_seconds = total_sleep_seconds / count

        avg_wake_time = f"{int(avg_wake_seconds // 3600)}:{int((avg_wake_seconds % 3600) // 60):02d}"
        avg_sleep_time = f"{int(avg_sleep_seconds // 3600)}:{int((avg_sleep_seconds % 3600) // 60):02d}"

        return avg_wake_time, avg_sleep_time
    else:
        return "00:00", "00:00"


def get_meeting_statistics(user, year, month):
    """Helper function to calculate meeting statistics for a given user, year, and month."""
    meetings = Meetings.objects.filter(
        user=user,
        date__year=year,
        date__month=month,
    )

    meetings_count = meetings.count()

    # Meeting type with the lowest positivity rating
    lowest_rating_meeting = meetings.order_by("positivity_rating").first()

    if lowest_rating_meeting:
        lowest_rating = lowest_rating_meeting.positivity_rating
        lowest_rating_type = lowest_rating_meeting.get_meeting_type_display()
    else:
        lowest_rating = None
        lowest_rating_type = None

    # Most common meeting type
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


def get_seizure_statistics(user, year, month):
    """Helper function to calculate seizure statistics for a given user, year, and month."""
    seizures = SeizureLog.objects.filter(
        user=user,
        date__year=year,
        date__month=month,
    )

    seizures_count = seizures.count()

    if seizures_count > 0:
        # Calculate average time of seizure occurrence (in seconds since midnight)
        seizures = seizures.annotate(
            seizure_seconds=ExpressionWrapper(
                F("time__hour") * 3600 + F("time__minute") * 60 + F("time__second"),
                output_field=IntegerField(),
            )
        )

        avg_seizure_time_seconds = seizures.aggregate(
            avg_seizure_time=Avg("seizure_seconds")
        )["avg_seizure_time"]

        avg_seizure_time = str(timedelta(seconds=avg_seizure_time_seconds))

        # Calculate average duration of seizures in minutes
        avg_seizure_duration = seizures.aggregate(avg_duration=Avg("duration_minutes"))[
            "avg_duration"
        ]

    else:
        avg_seizure_time = None
        avg_seizure_duration = None

    return {
        "seizures_count": seizures_count,
        "avg_seizure_time": avg_seizure_time,
        "avg_seizure_duration": avg_seizure_duration,
    }


def get_previous_event(user, date, time):
    # Retrieve the most recent food log entries for breakfast, lunch, and dinner
    food_logs = FoodLog.objects.filter(user=user, date=date)

    # Initialize variables to hold the most recent meal times
    latest_food_log = None
    latest_meal_time = None

    # Check each food log entry for the three meal times
    for food_log in food_logs:
        # Check breakfast time
        if food_log.breakfast_time and food_log.breakfast_time < time:
            if latest_meal_time is None or food_log.breakfast_time > latest_meal_time:
                latest_meal_time = food_log.breakfast_time
                latest_food_log = food_log

        # Check lunch time
        if food_log.lunch_time and food_log.lunch_time < time:
            if latest_meal_time is None or food_log.lunch_time > latest_meal_time:
                latest_meal_time = food_log.lunch_time
                latest_food_log = food_log

        # Check dinner time
        if food_log.dinner_time and food_log.dinner_time < time:
            if latest_meal_time is None or food_log.dinner_time > latest_meal_time:
                latest_meal_time = food_log.dinner_time
                latest_food_log = food_log

    # Retrieve the latest sport log entry before the seizure time
    sport_log = (
        SportLog.objects.filter(user=user, date=date, sport_time__lt=time)
        .order_by("-sport_time")
        .first()
    )

    # Retrieve the latest meeting log entry before the seizure time
    meeting_log = (
        Meetings.objects.filter(user=user, date=date, time__lt=time)
        .order_by("-time")
        .first()
    )

    # Create a list of the latest events
    events = []

    if latest_food_log:
        # Create a custom event with a unified time for FoodLog
        events.append((latest_meal_time, "Food", latest_food_log))

    if sport_log:
        events.append((sport_log.sport_time, "Sport", sport_log))

    if meeting_log:
        events.append((meeting_log.time, "Meeting", meeting_log))

    if not events:
        return None, None

    # Find the latest event overall based on the custom tuple (time, type, event)
    previous_event = max(events, key=lambda event: event[0])

    return previous_event[1], previous_event[2]  # Return the type and the event


def get_seizure_statistics_with_previous_event(user, year, month):
    # Retrieve seizures for the specified month
    seizures = SeizureLog.objects.filter(user=user, date__year=year, date__month=month)

    seizures_data = []
    for seizure in seizures:
        event_type, previous_event = get_previous_event(
            user, seizure.date, seizure.time
        )
        seizures_data.append(
            {
                "seizure": seizure,
                "previous_event_type": event_type,
                "previous_event": previous_event,
            }
        )

    return seizures_data


def get_medication_statistics(user, month, year):
    # Get the first day of the month as a date object
    first_day_of_month = datetime(year, month, 1).date()  # Convert to date

    # For the current month, the last day is today's date
    if year == datetime.now().year and month == datetime.now().month:
        last_day_of_month = datetime.now().date()  # This is already a date object
    else:
        # For past months, calculate the last day of the month
        # Start from the first day of the next month
        next_month = month % 12 + 1
        next_month_year = year if month < 12 else year + 1
        first_day_of_next_month = datetime(next_month_year, next_month, 1).date()

        # The last day of the current month is one day before the first day of the next month
        last_day_of_month = first_day_of_next_month - timedelta(days=1)

    # Now `first_day_of_month` and `last_day_of_month` are both date objects
    # Query all medication logs for the user in the given month
    medication_logs = MedicationLog.objects.filter(
        user=user, date__range=[first_day_of_month, last_day_of_month]
    )

    # Get a list of all days in the month
    all_days_in_month = [
        first_day_of_month + timedelta(days=i)
        for i in range((last_day_of_month - first_day_of_month).days + 1)
    ]

    # Organize the medication logs by medication
    medications = Medication.objects.filter(
        user=user
    )  # Get all medications for the user
    medication_stats = []

    for medication in medications:
        # Get the medication logs for this medication
        logs_for_medication = medication_logs.filter(medication=medication)

        # Get a set of days when the medication was taken
        days_taken = set(logs_for_medication.values_list("date", flat=True))

        # Calculate missed days (days when medication was not taken)
        missed_days = [day for day in all_days_in_month if day not in days_taken]

        # Add statistics for this medication
        medication_stats.append(
            {
                "medication": medication.name,
                "days_missed": len(missed_days),
                "missed_days_list": missed_days,
            }
        )

    return medication_stats
