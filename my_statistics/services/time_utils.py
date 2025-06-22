from datetime import timedelta, time
from datetime import time


def average_time(time_values):
    """Calculates the average time from a list of time objects."""
    valid_times = [t for t in time_values if t is not None]
    if not valid_times:
        return None

    total_seconds = sum(t.hour * 3600 + t.minute * 60 + t.second for t in valid_times)
    avg_seconds = total_seconds // len(valid_times)
    hours = avg_seconds // 3600
    minutes = (avg_seconds % 3600) // 60
    seconds = avg_seconds % 60

    return time(hour=hours, minute=minutes, second=seconds)



def time_to_seconds(t: time) -> int:
    if t is None:
        return 0
    return t.hour * 3600 + t.minute * 60 + t.second

def seconds_to_time_str(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}:{minutes:02d}"

