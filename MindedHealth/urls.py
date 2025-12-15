"""
URL configuration for MindedHealth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home   ')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from users.views import (
    home,
    about,
    features,
    register,
    login_view,
    custom_logout_view,
    therapist_page,
    family_member_page,
    keep_alive,
    room,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import IsAdminUser
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views


schema_view = get_schema_view(
   openapi.Info(
      title="Your API",
      default_version='v1',
      description="API documentation",
   ),
   public=False,
   permission_classes=(IsAdminUser,),
)

urlpatterns = [
    path("silk/", include("silk.urls", namespace="silk")),
    path("admin/", admin.site.urls),
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
    path("", home, name="home"),
    path('about/', about, name='about_us'),
    path('features/', features, name='features'),
    path("register/", register, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", custom_logout_view, name="logout"),
    path("medications/", include("medications.urls", namespace="medications")),
    path(
        "my_statistics/",
        include(("my_statistics.urls", "my_statistics"), namespace="my_statistics"),
    ),
    path("therapist/", therapist_page, name="therapist_dashboard"),
    path("family-member/", family_member_page, name="family_member_page"),
    path("what_interested_you/", include("what_interested_you.urls")),
    path("keep-alive/", keep_alive, name="keep_alive"),
    path("chat/<str:room_name>/", login_required(room), name="chat_room"),
    path("chatbot/", include("chatbot.urls")),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path("insights/", include("insights.urls")),
    path('users/', include('users.urls')), 
    path("api-token-auth/", obtain_auth_token, name="api_token_auth"),
        path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html',
        email_template_name='password_reset_email.html',  # email content
        subject_template_name='password_reset_subject.txt',
    ), name='password_reset'),

    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),

]
