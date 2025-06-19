from dashboard.models import SeizureLog
from rest_framework.exceptions import NotFound

def get_seizure_logs(user, date):
    return SeizureLog.objects.filter(user=user, date=date)

def get_seizure_log_or_404(pk):
    try:
        return SeizureLog.objects.get(pk=pk)
    except SeizureLog.DoesNotExist:
        raise NotFound("Seizure log not found.")

def create_or_update_seizure_log(user, data):
    date = data.get("date")
    SeizureLog.objects.update_or_create(user=user, date=date, defaults=data)

def update_seizure_log(seizure_log, data):
    for key, value in data.items():
        setattr(seizure_log, key, value)
    seizure_log.save()
    return seizure_log

def delete_seizure_log(seizure_log):
    seizure_log.delete()
