# medications/urls.py
from django.urls import path
from .views import MedicationListView, MedicationListCreateView, MedicationDeleteView,UpdateMedicationView, AddMedicationLogView

app_name = 'medications'  # Specify the app_name for namespacing


urlpatterns = [
    path('list/', MedicationListView.as_view(), name='list'),  # Adjust URL pattern and view name accordingly
    path('', MedicationListView.as_view(), name='medication_list'),
    path('api/medications/', MedicationListCreateView.as_view(), name='medication_list_create'),
    path('api/medications/<int:pk>/', MedicationDeleteView.as_view(), name='medication_delete'),
    path('update/', UpdateMedicationView.as_view(), name='update'),
    path('update/<int:pk>/', UpdateMedicationView.as_view(), name='update'),
    path('add-medication-log/', AddMedicationLogView.as_view(), name='add_medication_log'),



]