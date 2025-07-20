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
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from . import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="MindedHealth API",
      default_version='v1',
      description="API documentation for MindedHealth",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="support@mindedhealth.com"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
    
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.custom_logout_view, name="logout"),
    path("medications/", include("medications.urls", namespace="medications")),
    path(
        "my_statistics/",
        include(("my_statistics.urls", "my_statistics"), namespace="my_statistics"),
    ),
    path("what_interested_you/", include("what_interested_you.urls")),
    path("keep-alive/", views.keep_alive, name="keep_alive"),
    path("chat/<str:room_name>/", views.room, name="chat_room"),
    path("chatbot/", include("chatbot.urls")),
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("insights/", include("insights.urls")),
]
