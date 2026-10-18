from django.urls import path

from . import views

app_name = 'therapist_portal'

urlpatterns = [
    path('patient/<int:patient_id>/unassign/', views.unassign_patient, name='unassign_patient'),
    # Remaining routes land here one at a time as each view PR merges
    # (patient_documentation, patient_seizures, patient_medications, patient_alerts).
]
