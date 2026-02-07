from rest_framework import serializers
from .models import Medication

class MedicationSerializer(serializers.ModelSerializer):
    dose_times = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list
    )

    class Meta:
        model = Medication
        fields = ["id", "name", "times_per_day", "dose", "dose_times", "user"]
        read_only_fields = ["user"]

