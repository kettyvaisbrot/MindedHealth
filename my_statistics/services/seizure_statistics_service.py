from dashboard.models import SeizureLog
from my_statistics.services.event_service import get_previous_event

def fetch_seizure_data_with_previous_event(user, year, month):
    seizures = SeizureLog.objects.filter(user=user, date__year=year, date__month=month)

    seizures_data = []
    for seizure in seizures:
        event_type, previous_event = get_previous_event(user, seizure.date, seizure.time)
        seizures_data.append({
            "seizure": seizure,
            "previous_event_type": event_type,
            "previous_event": previous_event,
        })

    return seizures_data
