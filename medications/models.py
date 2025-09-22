from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class Medication(models.Model):
    name = models.CharField(max_length=255)
    times_per_day = (
        models.PositiveIntegerField()
    )
    dose = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dose_times = models.JSONField(
        default=list
    )

    def __str__(self):
        return self.name


class MedicationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    date = models.DateField()
    time_taken = models.TimeField()
    dose_index = models.IntegerField()
