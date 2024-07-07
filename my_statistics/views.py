from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, F, ExpressionWrapper, IntegerField, Count
from datetime import datetime, timedelta
from calendar import month_name
from dashboard.models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog

@login_required
def statistics_view(request):
    selected_month = request.GET.get('month', None)
    selected_year = request.GET.get('year', None)

    if not selected_month or not selected_year:
        current_date = datetime.now().date()
        selected_month = current_date.month
        selected_year = current_date.year

    selected_month = int(selected_month)
    selected_year = int(selected_year)

    # Generating month choices for the dropdown
    month_choices = [(month_num, month_name[month_num]) for month_num in range(1, 13)]

    # Retrieve statistics based on selected month and year
    breakfast_stats = get_avg_meal_time(request.user, selected_year, selected_month, 'breakfast')
    lunch_stats = get_avg_meal_time(request.user, selected_year, selected_month, 'lunch')
    dinner_stats = get_avg_meal_time(request.user, selected_year, selected_month, 'dinner')

    sport_stats = get_sport_statistics(request.user, selected_year, selected_month)
    sleep_stats = get_sleeping_statistics(request.user, selected_year, selected_month)
    meeting_stats = get_meeting_statistics(request.user, selected_year, selected_month)
    seizure_stats = get_seizure_statistics(request.user, selected_year, selected_month)

    context = {
        'breakfast_stats': breakfast_stats,
        'lunch_stats': lunch_stats,
        'dinner_stats': dinner_stats,
        'sport_stats': sport_stats,
        'sleep_stats': sleep_stats,
        'meeting_stats': meeting_stats,
        'seizure_stats': seizure_stats,
        'current_month': selected_month,
        'current_year': selected_year,
        'month_choices': month_choices,
    }

    return render(request, 'my_statistics/statistics.html', context)

def get_avg_meal_time(user, year, month, meal_type):
    """Helper function to calculate average meal time for a given user, year, month, and meal type."""
    meal_logs = FoodLog.objects.filter(
        user=user,
        date__year=year,
        date__month=month,
        **{f'{meal_type}_ate': True}
    ).exclude(**{f'{meal_type}_time__isnull': True}).annotate(
        **{f'{meal_type}_seconds': ExpressionWrapper(
            F(f'{meal_type}_time__hour') * 3600 + F(f'{meal_type}_time__minute') * 60 + F(f'{meal_type}_time__second'),
            output_field=IntegerField()
        )}
    )

    if meal_logs.exists():
        avg_time_seconds = meal_logs.aggregate(
            avg_time=Avg(f'{meal_type}_seconds')
        )['avg_time']
        avg_time = str(timedelta(seconds=avg_time_seconds))
    else:
        avg_time = None

    return avg_time

from django.db.models import Count

def get_sport_statistics(user, year, month):
    """Helper function to retrieve sport statistics for a given user, year, and month."""
    sport_logs = SportLog.objects.filter(
        user=user,
        date__year=year,
        date__month=month,
        did_sport=True
    ).annotate(
        sport_seconds=ExpressionWrapper(
            F('sport_time__hour') * 3600 + F('sport_time__minute') * 60 + F('sport_time__second'),
            output_field=IntegerField()
        )
    )

    sport_count = sport_logs.count()

    if sport_count > 0:
        avg_sport_time_seconds = sport_logs.aggregate(
            avg_sport_time=Avg('sport_seconds')
        )['avg_sport_time']
        avg_sport_time = str(timedelta(seconds=avg_sport_time_seconds))

        most_common_sport = sport_logs.values('sport_type').annotate(count=Count('sport_type')).order_by('-count').first()
        if most_common_sport:
            most_common_sport_activity = most_common_sport['sport_type']
        else:
            most_common_sport_activity = None
    else:
        avg_sport_time = None
        most_common_sport_activity = None

    return {
        'avg_sport_time': avg_sport_time,
        'sport_count': sport_count,
        'most_common_sport_activity': most_common_sport_activity,
    }

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
        'avg_wake_time': avg_wake_time,
        'avg_sleep_time': avg_sleep_time,
        'nights_awake_count': nights_awake_count,
        'days_count': days_count,
    }

def calculate_avg_sleep_times(sleeping_logs):
    """Helper function to calculate average wake time and sleep time from SleepingLog queryset."""
    total_wake_seconds = 0
    total_sleep_seconds = 0
    count = sleeping_logs.count()

    for log in sleeping_logs:
        total_wake_seconds += log.wake_time.hour * 3600 + log.wake_time.minute * 60 + log.wake_time.second
        total_sleep_seconds += log.sleep_time.hour * 3600 + log.sleep_time.minute * 60 + log.sleep_time.second

    if count > 0:
        avg_wake_seconds = total_wake_seconds / count
        avg_sleep_seconds = total_sleep_seconds / count
    else:
        avg_wake_seconds = 0
        avg_sleep_seconds = 0

    avg_wake_time = timedelta(seconds=avg_wake_seconds)
    avg_sleep_time = timedelta(seconds=avg_sleep_seconds)

    return avg_wake_time, avg_sleep_time


def get_meeting_statistics(user, year, month):
    """Helper function to calculate meeting statistics for a given user, year, and month."""
    meetings = Meetings.objects.filter(
        user=user,
        date__year=year,
        date__month=month,
    )

    meetings_count = meetings.count()

    # Meeting type with the lowest positivity rating
    lowest_rating_meeting = meetings.order_by('positivity_rating').first()

    if lowest_rating_meeting:
        lowest_rating = lowest_rating_meeting.positivity_rating
        lowest_rating_type = lowest_rating_meeting.get_meeting_type_display()
    else:
        lowest_rating = None
        lowest_rating_type = None

    # Most common meeting type
    most_common_meeting = meetings.values('meeting_type').annotate(count=Count('meeting_type')).order_by('-count').first()

    if most_common_meeting:
        most_common_meeting_type = most_common_meeting['meeting_type']
        most_common_meeting_count = most_common_meeting['count']
    else:
        most_common_meeting_type = None
        most_common_meeting_count = None

    return {
        'meetings_count': meetings_count,
        'lowest_rating': lowest_rating,
        'lowest_rating_type': lowest_rating_type,
        'most_common_meeting_type': most_common_meeting_type,
        'most_common_meeting_count': most_common_meeting_count,
    }

from django.db.models import F, ExpressionWrapper, IntegerField
from datetime import timedelta

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
                F('time__hour') * 3600 + F('time__minute') * 60 + F('time__second'),
                output_field=IntegerField()
            )
        )

        avg_seizure_time_seconds = seizures.aggregate(
            avg_seizure_time=Avg('seizure_seconds')
        )['avg_seizure_time']

        avg_seizure_time = str(timedelta(seconds=avg_seizure_time_seconds))

        # Calculate average duration of seizures in minutes
        avg_seizure_duration = seizures.aggregate(
            avg_duration=Avg('duration_minutes')
        )['avg_duration']

    else:
        avg_seizure_time = None
        avg_seizure_duration = None

    return {
        'seizures_count': seizures_count,
        'avg_seizure_time': avg_seizure_time,
        'avg_seizure_duration': avg_seizure_duration,
    }
