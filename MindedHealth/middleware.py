# middleware.py
from django.contrib.sessions.models import Session
from django.utils import timezone

class LogoutOnServerStartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logout_users()

    def logout_users(self):
        # Get the current time
        now = timezone.now()
        # Query all active sessions
        sessions = Session.objects.all()
        # Iterate through each session and delete it
        for session in sessions:
            session.delete()  # This will log out all users

    def __call__(self, request):
        # Here, you can include any request-specific logic if needed
        return self.get_response(request)
 