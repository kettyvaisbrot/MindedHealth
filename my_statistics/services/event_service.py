# statistics/services/event_service.py

from dashboard.models import FoodLog, SportLog, Meetings

def get_latest_meal_log(user, date, time):
    food_logs = FoodLog.objects.filter(user=user, date=date)
    latest_food_log = None
    latest_meal_time = None

    for food_log in food_logs:
        for meal_time in [("breakfast_time", food_log.breakfast_time),
                          ("lunch_time", food_log.lunch_time),
                          ("dinner_time", food_log.dinner_time)]:
            if meal_time[1] and meal_time[1] < time:
                if latest_meal_time is None or meal_time[1] > latest_meal_time:
                    latest_meal_time = meal_time[1]
                    latest_food_log = food_log

    if latest_food_log:
        return latest_meal_time, "Food", latest_food_log
    return None


def get_latest_sport_log(user, date, time):
    sport_log = (
        SportLog.objects.filter(user=user, date=date, sport_time__lt=time)
        .order_by("-sport_time")
        .first()
    )
    if sport_log:
        return sport_log.sport_time, "Sport", sport_log
    return None


def get_latest_meeting_log(user, date, time):
    meeting_log = (
        Meetings.objects.filter(user=user, date=date, time__lt=time)
        .order_by("-time")
        .first()
    )
    if meeting_log:
        return meeting_log.time, "Meeting", meeting_log
    return None


def get_previous_event(user, date, time):
    events = filter(None, [
        get_latest_meal_log(user, date, time),
        get_latest_sport_log(user, date, time),
        get_latest_meeting_log(user, date, time),
    ])

    previous_event = max(events, key=lambda event: event[0], default=None)

    if previous_event:
        return previous_event[1], previous_event[2]  # type, object
    return None, None
