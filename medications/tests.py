from django.test import TestCase,Client
from django.contrib.auth import get_user_model
from .models import Medication, MedicationLog
from datetime import date, time
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import datetime


User = get_user_model()

class MedicationsModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.medication = Medication.objects.create(
            name="Aspirin",
            times_per_day=2,
            dose="500mg",
            user=self.user,
            dose_times=["08:00", "20:00"]
        )

    def test_medication_creation(self):
        self.assertEqual(self.medication.name, "Aspirin")
        self.assertEqual(self.medication.times_per_day, 2)
        self.assertEqual(self.medication.dose, "500mg")
        self.assertEqual(self.medication.user, self.user)
        self.assertEqual(self.medication.dose_times, ["08:00", "20:00"])

    def test_medication_str(self):
        self.assertEqual(str(self.medication), "Aspirin")

    def test_medication_log_creation(self):
        med_log = MedicationLog.objects.create(
            user=self.user,
            medication=self.medication,
            date=date.today(),
            time_taken=time(8, 0),
            dose_index=0
        )
        self.assertEqual(med_log.user, self.user)
        self.assertEqual(med_log.medication, self.medication)
        self.assertEqual(med_log.dose_index, 0)
        self.assertEqual(med_log.time_taken, time(8, 0))


class MedicationsViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="password123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="otheruser@example.com", password="password123"
        )
        self.med1 = Medication.objects.create(
            name="Med1",
            times_per_day=2,
            dose="10mg",
            user=self.user,
            dose_times=["08:00", "20:00"]
        )
        self.med2 = Medication.objects.create(
            name="Med2",
            times_per_day=1,
            dose="5mg",
            user=self.user,
            dose_times=["09:00"]
        )

        self.client = Client()
        self.api_client = APIClient()

    def test_medications_page_view_authenticated(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("medications_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "medications/medications_page.html")

    def test_medications_page_view_unauthenticated(self):
        response = self.client.get(reverse("medications_page"))
        self.assertEqual(response.status_code, 302)


    # API Tests

    def test_list_medications(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.get("/medications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_medication(self):
        self.api_client.force_authenticate(user=self.user)
        data = {
            "name": "Med3",
            "times_per_day": 3,
            "dose": "15mg",
            "dose_times": ["08:00", "14:00", "20:00"]
        }
        response = self.api_client.post("/medications/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Medication.objects.filter(user=self.user).count(), 3)

    def test_update_medication(self):
        self.api_client.force_authenticate(user=self.user)
        data = {"name": "Updated Med1", "times_per_day": 2, "dose": "20mg", "dose_times": ["08:00", "20:00"]}
        response = self.api_client.put(f"/medications/{self.med1.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.med1.refresh_from_db()
        self.assertEqual(self.med1.name, "Updated Med1")
        self.assertEqual(self.med1.dose, "20mg")

    def test_delete_medication(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.delete(f"/medications/{self.med1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Medication.objects.filter(id=self.med1.id).exists())

    def test_log_medication(self):
        self.api_client.force_authenticate(user=self.user)
        data = {
            "medication_id": self.med2.id,
            "date": str(datetime.date.today()),
            "time_taken": "09:00:00",
            "dose_index": 0
        }
        response = self.api_client.post("/medications/log/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MedicationLog.objects.filter(user=self.user, medication=self.med2).exists())