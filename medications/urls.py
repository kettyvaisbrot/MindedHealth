from django.urls import path, include
from rest_framework import routers
from .views import MedicationViewSet, medications_page

router = routers.DefaultRouter()
router.register(r'medications', MedicationViewSet, basename='medication')

app_name = "medications"

urlpatterns = [
    path('', medications_page, name='medications_page'),   
    path('api/', include(router.urls)),                   
]
