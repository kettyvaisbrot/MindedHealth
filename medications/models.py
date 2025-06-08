# models.py
from django.db import models
from django.contrib.auth.models import User


class Medication(models.Model):
    name = models.CharField(max_length=255)
    times_per_day = (
        models.PositiveIntegerField()
    )  # Times per day the medication should be taken
    dose = models.CharField(max_length=255)  # Medication dose details
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dose_times = models.JSONField(
        default=list
    )  # List of time strings (e.g., ["08:00", "14:00", "20:00"])

    def __str__(self):
        return self.name


class MedicationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    date = models.DateField()
    time_taken = models.TimeField()
    dose_index = models.IntegerField()
