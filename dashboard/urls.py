from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import (
    CategorySummaryView,
    CategoryEditView,
    CategoryChatView,
    CategoryChatSubmitView,
    category_summary_page,

)


app_name = "dashboard"

urlpatterns = [
    path('log/<str:category>/summary/', category_summary_page, name='category_summary'),
    path('api/log/<str:category>/summary/', CategorySummaryView.as_view(), name='api_category_summary'),
    path('log/<str:category>/edit/', CategoryEditView.as_view(), name='category_edit'),
    path('api/chat/<str:category>/', CategoryChatView.as_view(), name='category_chat_api'),
    path("chat/<str:category>/", views.chat_page, name="category_chat_page"),
    path('log/<str:category>/chat/', views.chat_page, name='category_chat'),
    path('log/<str:category>/chat/submit/', CategoryChatSubmitView.as_view(), name='category_chat_submit'),
    path("", views.dashboard_home, name="dashboard_home"),
    path('log/<str:category>/', views.log_category, name='log_category'),
    path("<str:date>/", views.dashboard_home, name="dashboard_home_with_date"),
    path("keep-alive/", views.keep_alive, name="keep_alive"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
