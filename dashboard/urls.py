from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views


app_name = 'dashboard'  # Define the app_name here


urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),  # Default to today's date
    path('<str:date>/', views.dashboard_home, name='dashboard_home_with_date'),
    path('api/food/', views.FoodLogAPIView.as_view(), name='food_log_api'),  # For POST requests
    path('api/food/<str:date>/', views.FoodLogAPIView.as_view(), name='food_log_api'),
    path('api/sport/', views.SportLogAPIView.as_view(), name='sport_log_api'),  # For POST requests
    path('api/sport/<str:date>/', views.SportLogAPIView.as_view(), name='sport_log_api'),
    path('api/sleeping/', views.SleepingLogAPIView.as_view(), name='sleeping_log_api'),  # For POST requests
    path('api/sleeping/<str:date>/', views.SleepingLogAPIView.as_view(), name='sleeping_log_api'),
    path('api/meetings/', views.MeetingsAPIView.as_view(), name='meetings_log_api'),  # For POST requests
    path('api/meetings/<str:date>/', views.MeetingsAPIView.as_view(), name='meetings_log_api'),  # For GET requests
    path('api/seizure-logs/', views.SeizureLogAPIView.as_view(), name='seizure_logs_api'),
    path('api/seizure-logs/<str:date>/', views.SeizureLogAPIView.as_view(), name='seizure_logs_api'),
    path('log_medication/<str:date>/', views.log_medication, name='log_medication'),  # Ensure the date parameter is included
    path('dashboard/<str:date>/', views.dashboard_home, name='dashboard_home_with_date'),
    path('keep-alive/', views.keep_alive, name='keep_alive'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),




    
]











