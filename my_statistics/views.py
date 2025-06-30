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
from my_statistics.services.statistics_service import calculate_avg_meal_time
from my_statistics.services.sport_statistics_service import fetch_sport_statistics
from my_statistics.services.sleeping_statistics_service import fetch_sleeping_statistics
from my_statistics.services.sleeping_statistics_service import calculate_avg_sleep_times as service_calculate_avg_sleep_times
from my_statistics.services.statistics_service import get_meeting_statistics_service
from my_statistics.services.statistics_service import compute_seizure_statistics
from my_statistics.services.event_service import get_previous_event as service_get_previous_event
from my_statistics.services.seizure_statistics_service import fetch_seizure_data_with_previous_event
from my_statistics.services.statistics_service import get_medication_statistics
from django.http import HttpResponseServerError
import traceback

def gather_statistics_for_user(user, year, month):
    breakfast_stats = get_avg_meal_time(user, year, month, "breakfast")
    lunch_stats = get_avg_meal_time(user, year, month, "lunch")
    dinner_stats = get_avg_meal_time(user, year, month, "dinner")

    sport_stats = get_sport_statistics(user, year, month)
    sleep_stats = get_sleeping_statistics(user, year, month)
    meeting_stats = get_meeting_statistics(user, year, month)
    seizure_stats = get_seizure_statistics(user, year, month)
    seizure_stats_with_events = get_seizure_statistics_with_previous_event(user, year, month)
    medication_statistics = get_medication_statistics(user, month, year)

    days_in_month = calendar.monthrange(year, month)[1]
    sleep_durations = {}

    for day in range(1, days_in_month + 1):
        current_date = datetime(year, month, day).date()
        sleep_log = SleepingLog.objects.filter(date=current_date, user=user).first()

        if sleep_log and sleep_log.went_to_sleep_yesterday and sleep_log.wake_up_time:
            sleep_time = datetime.combine(current_date, sleep_log.went_to_sleep_yesterday)
            wake_up_time = datetime.combine(current_date, sleep_log.wake_up_time)

            if wake_up_time <= sleep_time:
                wake_up_time += timedelta(days=1)

            duration = wake_up_time - sleep_time

            sleep_durations[current_date] = {
                "days": duration.days,
                "hours": duration.seconds // 3600,
                "minutes": (duration.seconds // 60) % 60,
            }

    month_choices = [(m, calendar.month_name[m]) for m in range(1, 13)]

    return {
        "breakfast_stats": breakfast_stats,
        "lunch_stats": lunch_stats,
        "dinner_stats": dinner_stats,
        "sport_stats": sport_stats,
        "sleep_stats": sleep_stats,
        "meeting_stats": meeting_stats,
        "seizure_stats": seizure_stats,
        "seizure_stats_with_events": seizure_stats_with_events,
        "medication_statistics": medication_statistics,
        "sleep_durations": sleep_durations,
        "month_choices": month_choices,
        "current_month": month,
        "current_year": year,
    }


def keep_alive(request):
    # Simply return a success response to reset the session timer
    return JsonResponse({"status": "success"})


@login_required
def statistics_view(request):
    selected_month = request.GET.get("month")
    selected_year = request.GET.get("year")

    if not selected_month or not selected_year:
        now = datetime.now()
        selected_month = now.month
        selected_year = now.year

    selected_month = int(selected_month)
    selected_year = int(selected_year)

    try:
        context = gather_statistics_for_user(request.user, selected_year, selected_month)
        return render(request, "my_statistics/statistics.html", context)

    except Exception as e:
        print("==== ERROR in statistics_view ====")
        traceback.print_exc()
        return HttpResponseServerError("An error occurred while generating statistics.")



def get_avg_meal_time(user, year, month, meal_type):
    return calculate_avg_meal_time(user, year, month, meal_type)

def get_sport_statistics(user, year, month):
    return fetch_sport_statistics(user, year, month)

def convert_seconds_to_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return hours, minutes

def get_sleeping_statistics(user, year, month):
    return fetch_sleeping_statistics(user, year, month)

def calculate_avg_sleep_times(sleeping_logs):
    # Simply delegate to the service function
    return service_calculate_avg_sleep_times(sleeping_logs)

def get_meeting_statistics(user, year, month):
    return get_meeting_statistics_service(user, year, month)

def get_seizure_statistics(user, year, month):
    return compute_seizure_statistics(user, year, month)

def get_previous_event(user, date, time):
    return service_get_previous_event(user, date, time)

def get_seizure_statistics_with_previous_event(user, year, month):
    return fetch_seizure_data_with_previous_event(user, year, month)

def get_medication_statistics(user, year, month):
    return get_medication_statistics(user, year, month)