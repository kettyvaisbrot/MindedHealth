from django.urls import path
from . import views

urlpatterns = [
    path(
        "api/chat/", views.chatbot_response, name="chatbot_response"
    ),
    path("", views.chatbot_page, name="chatbot_page"),
]
