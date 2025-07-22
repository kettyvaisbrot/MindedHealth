from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .serializers import MedicationSerializer
from .models import Medication
from .services import log_medication_service, delete_medication
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def medications_page(request):
    return render(request, "medications/medications_page.html")


class MedicationViewSet(viewsets.ModelViewSet):
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



    @action(detail=False, methods=['post'], url_path='log')
    def log_medication(self, request):
        serializer = LogMedicationSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        log_medication_service(
            user=request.user,
            medication_id=serializer.validated_data["medication_id"],
            date=serializer.validated_data["date"],
            time_taken=serializer.validated_data["time_taken"],
            dose_index=serializer.validated_data["dose_index"],
        )

        return Response({"detail": "Medication logged successfully"}, status=status.HTTP_201_CREATED)

