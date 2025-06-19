from dashboard.models import Meetings
from rest_framework.exceptions import NotFound

def get_meetings_by_date(user, date):
    return Meetings.objects.filter(user=user, date=date)

def get_meeting_or_404(pk):
    try:
        return Meetings.objects.get(pk=pk)
    except Meetings.DoesNotExist:
        raise NotFound("Meeting not found.")

def create_or_update_meeting(user, data):
    date = data.get("date")
    Meetings.objects.update_or_create(user=user, date=date, defaults=data)

def update_meeting(meeting, data):
    for key, value in data.items():
        setattr(meeting, key, value)
    meeting.save()
    return meeting

def delete_meeting(meeting):
    meeting.delete()
