import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MindedHealth.settings")

from django.core.asgi import get_asgi_application

# Must run before importing routing/consumers, which import models -- those
# need the app registry ready first.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from MindedHealth import routing

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(routing.websocket_urlpatterns)),
    }
)
