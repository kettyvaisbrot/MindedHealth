from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "dashboard"

urlpatterns = [
    path('log/<str:category>/summary/', views.category_summary, name='category_summary'),
    path('log/<str:category>/edit/', views.category_edit, name='category_edit'),
    path('log/<str:category>/update/', views.category_update, name='category_update'),
    path('log/<str:category>/chat/', views.category_chat_page, name='category_chat'),
    path('log/<str:category>/chat/force/', views.category_chat_force, name='category_chat_force'),
    path('log/<str:category>/chat/submit/', views.category_chat_submit, name='category_chat_submit'),
    path("", views.dashboard_home, name="dashboard_home"),
    path('log/<str:category>/', views.log_category, name='log_category'),
    path("<str:date>/", views.dashboard_home, name="dashboard_home_with_date"),
    path("keep-alive/", views.keep_alive, name="keep_alive"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
