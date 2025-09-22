# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('therapist-dashboard/', views.therapist_dashboard, name='therapist_dashboard'),
    path('family-dashboard/<int:family_member_id>/', views.family_dashboard, name='family_dashboard'),
]
