# middleware.py
from django.contrib.sessions.models import Session
from django.utils import timezone

class LogoutOnServerStartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logout_users()

    def logout_users(self):
        now = timezone.now()
        sessions = Session.objects.all()
        for session in sessions:
            session.delete()  

    def __call__(self, request):
        return self.get_response(request)
 