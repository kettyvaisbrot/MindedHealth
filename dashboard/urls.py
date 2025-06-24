from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = "dashboard"


urlpatterns = [
    path("", views.dashboard_home, name="dashboard_home"),
    path("api/food/", views.FoodLogAPIView.as_view(), name="food_log_api"),
    path("api/food/<str:date>/", views.FoodLogAPIView.as_view(), name="food_log_api"),
    path("api/sport/", views.SportLogAPIView.as_view(), name="sport_log_api"),
    path(
        "api/sport/<str:date>/", views.SportLogAPIView.as_view(), name="sport_log_api"
    ),
    path("api/sleeping/", views.SleepingLogAPIView.as_view(), name="sleeping_log_api"),
    path(
        "api/sleeping/<str:date>/",
        views.SleepingLogAPIView.as_view(),
        name="sleeping_log_api",
    ),
    path("api/meetings/", views.MeetingsAPIView.as_view(), name="meetings_log_api"),
    path(
        "api/meetings/<str:date>/",
        views.MeetingsAPIView.as_view(),
        name="meetings_log_api",
    ),
    path(
        "api/seizure-logs/", views.SeizureLogAPIView.as_view(), name="seizure_logs_api"
    ),
    path(
        "api/seizure-logs/<str:date>/",
        views.SeizureLogAPIView.as_view(),
        name="seizure_logs_api",
    ),
    path("log_medication/<str:date>/", views.log_medication, name="log_medication"),
    path("keep-alive/", views.keep_alive, name="keep_alive"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
