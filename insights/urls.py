from django.urls import path
from .views import AIInsightsAPIView, insights_page_view

app_name = "insights" 


urlpatterns = [
    path('api/insights/', AIInsightsAPIView.as_view(), name='ai_insight_api'),
    path('', insights_page_view, name='ai_insight_page'),
]
