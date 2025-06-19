from dashboard.models import SleepingLog
from rest_framework.exceptions import NotFound

def get_sleeping_logs(user, date):
    return SleepingLog.objects.filter(user=user, date=date)

def get_sleeping_log_or_404(user, date):
    sleeping_log = SleepingLog.objects.filter(user=user, date=date).first()
    if not sleeping_log:
        raise NotFound("Sleeping log not found for this date")
    return sleeping_log

def create_or_update_sleeping_log(user, data):
    date = data.get("date")
    SleepingLog.objects.update_or_create(user=user, date=date, defaults=data)

def update_sleeping_log(sleeping_log, data):
    for key, value in data.items():
        setattr(sleeping_log, key, value)
    sleeping_log.save()
    return sleeping_log

def delete_sleeping_log(sleeping_log):
    sleeping_log.delete()
