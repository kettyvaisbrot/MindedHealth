from dashboard.models import SportLog
from rest_framework.exceptions import NotFound

def get_sport_logs(user, date):
    return SportLog.objects.filter(user=user, date=date)

def get_sport_log_or_404(user, date):
    sport_log = SportLog.objects.filter(user=user, date=date).first()
    if not sport_log:
        raise NotFound("Sport log not found for this date")
    return sport_log

def create_or_update_sport_log(user, data):
    date = data.get("date")
    SportLog.objects.update_or_create(user=user, date=date, defaults=data)

def update_sport_log(sport_log, data):
    for key, value in data.items():
        setattr(sport_log, key, value)
    sport_log.save()
    return sport_log

def delete_sport_log(sport_log):
    sport_log.delete()
