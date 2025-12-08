from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('therapist', 'Therapist'),
        ('family', 'Family Member'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')


class TherapistProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.specialization})"


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    therapist = models.ForeignKey(
        TherapistProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="patients"
    )

    def __str__(self):
        return f"{self.user.username} (Therapist: {self.therapist.user.username if self.therapist else 'None'})"


class FamilyMemberProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    related_patient = models.OneToOneField(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='family_member'
    )
    relation = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} -> {self.related_patient.user.username}"
