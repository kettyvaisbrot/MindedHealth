from django.urls import path

from . import views

app_name = 'therapist_portal'

urlpatterns = [
    path('patient/<int:patient_id>/unassign/', views.unassign_patient, name='unassign_patient'),
    path('patient/<int:patient_id>/documentation/', views.patient_documentation, name='patient_documentation'),
    path('patient/<int:patient_id>/seizures/', views.patient_seizures, name='patient_seizures'),
    # Remaining routes land here one at a time as each view PR merges
    # (patient_medications, patient_alerts).
]
