# medications/urls.py
from django.urls import path
from .views import (
    medication_list,
    add_medication,
    edit_medication,
    delete_medication,
    log_medication,
    keep_alive,
)
from django.contrib.auth import views as auth_views

app_name = "medications"

urlpatterns = [
    path("", medication_list, name="medication_list"),
    path("add/", add_medication, name="add_medication"),
    path("edit/<int:pk>/", edit_medication, name="edit_medication"),
    path("delete/<int:pk>/", delete_medication, name="delete_medication"),
    path("log/", log_medication, name="log_medication"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("keep-alive/", keep_alive, name="keep_alive"),
]
