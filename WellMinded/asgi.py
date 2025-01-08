import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from WellMinded import routing  # Import the routing file

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WellMinded.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns  # Make sure the WebSocket URL patterns are included
        )
    ),
})
