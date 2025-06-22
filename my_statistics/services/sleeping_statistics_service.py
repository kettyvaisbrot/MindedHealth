from dashboard.models import SleepingLog
from .time_utils import average_time
from .time_utils import time_to_seconds, seconds_to_time_str

def fetch_sleeping_statistics(user, year, month):
    logs = SleepingLog.objects.filter(
        user=user,
        date__year=year,
        date__month=month,
    )

    days_count = logs.count()

    if days_count == 0:
        return {
            "avg_wake_time": None,
            "avg_sleep_time": None,
            "nights_awake_count": None,
            "days_count": 0,
        }

    avg_wake_time = _get_avg_time_from_logs(logs, "wake_up_time")
    avg_sleep_time = _get_avg_time_from_logs(logs, "went_to_sleep_yesterday")
    nights_awake_count = logs.filter(woke_up_during_night=True).count()

    return {
        "avg_wake_time": avg_wake_time,
        "avg_sleep_time": avg_sleep_time,
        "nights_awake_count": nights_awake_count,
        "days_count": days_count,
    }

def _get_avg_time_from_logs(logs, field_name):
    time_values = logs.values_list(field_name, flat=True)
    return average_time(time_values)

def calculate_avg_sleep_times(sleeping_logs):
    total_wake_seconds = 0
    total_sleep_seconds = 0
    count = 0

    for log in sleeping_logs:
        if log.wake_up_time and log.went_to_sleep_yesterday:
            total_wake_seconds += time_to_seconds(log.wake_up_time)
            total_sleep_seconds += time_to_seconds(log.went_to_sleep_yesterday)
            count += 1

    if count == 0:
        return "00:00", "00:00"

    avg_wake_seconds = total_wake_seconds / count
    avg_sleep_seconds = total_sleep_seconds / count

    avg_wake_time = seconds_to_time_str(avg_wake_seconds)
    avg_sleep_time = seconds_to_time_str(avg_sleep_seconds)

    return avg_wake_time, avg_sleep_time