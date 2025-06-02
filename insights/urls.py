from django.urls import path
from .views import ai_insights_view

urlpatterns = [
    path('', ai_insights_view, name='ai_insight'),
]
