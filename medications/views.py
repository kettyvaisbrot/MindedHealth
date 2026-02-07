from rest_framework import viewsets, permissions
from .serializers import MedicationSerializer
from .models import Medication
from .services import delete_medication
from django.contrib.auth.decorators import login_required
from django.shortcuts import render



@login_required
def medications_page(request):
    return render(request, "medications/medications_page.html")


class MedicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing medications.
    - List, retrieve, create, update, and delete medications for the authenticated user.
    """
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        delete_medication(instance)

