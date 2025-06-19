from dashboard.models import FoodLog
from rest_framework.exceptions import NotFound

def get_food_logs(user, date):
    return FoodLog.objects.filter(user=user, date=date)

def get_food_log_or_404(user, date):
    food_log = FoodLog.objects.filter(user=user, date=date).first()
    if not food_log:
        raise NotFound("Food log not found for this date")
    return food_log

def create_or_update_food_log(user, data):
    date = data.get("date")
    FoodLog.objects.update_or_create(user=user, date=date, defaults=data)

def update_food_log(food_log, data):
    for key, value in data.items():
        setattr(food_log, key, value)
    food_log.save()
    return food_log

def delete_food_log(food_log):
    food_log.delete()
