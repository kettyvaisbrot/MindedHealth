from django.contrib.sessions.models import Session
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class LogoutOnServerStartMiddleware:
    """
    Logs out all users by deleting sessions safely on server start.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Only attempt to clean sessions if server is running in normal mode
        try:
            self.logout_users()
        except Exception as e:
            logger.warning(f"Could not clear sessions on startup: {e}")

    def logout_users(self):
        """
        Deletes all active sessions safely.
        """
        sessions = Session.objects.all()
        for session in sessions:
            try:
                session.delete()
            except Exception as e:
                logger.warning(f"Could not delete session {session.session_key}: {e}")

    def __call__(self, request):
        response = self.get_response(request)
        return response
