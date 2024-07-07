from rest_framework import serializers
from .models import Medication, MedicationLog

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ['id', 'name', 'times_per_day', 'dose', 'user']
        read_only_fields = ['user']  # Ensure 'user' is read-only

class MedicationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationLog
        fields = ['id', 'medication', 'date', 'time_taken','user']
