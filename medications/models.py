# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import datetime
from django.conf import settings



class Medication(models.Model):
    name = models.CharField(max_length=255)
    times_per_day = models.IntegerField()
    dose = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class MedicationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    date = models.DateField()
    time_taken = models.TimeField(default=datetime.time(0, 0))

    def __str__(self):
        return f"{self.medication.name} - {self.date}"
