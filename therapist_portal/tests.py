from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import PatientProfile, TherapistProfile, User


@override_settings(
    SESSION_ENGINE='django.contrib.sessions.backends.db',
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class UnassignPatientTests(TestCase):
    def setUp(self):
        # Force the test client's middleware chain to load *before* any
        # force_login() call. Django's test Client builds its middleware
        # lazily on the first real request; this project's
        # LogoutOnServerStartMiddleware wipes every session on that first
        # load, which would otherwise delete the session force_login just
        # created and silently log the test user back out.
        self.client.get('/keep-alive/')

        self.therapist_user = User.objects.create_user(
            username='therapist1', email='therapist1@example.com',
            password='pass12345', role='therapist',
        )
        self.therapist_profile = TherapistProfile.objects.create(user=self.therapist_user)

        self.other_therapist_user = User.objects.create_user(
            username='therapist2', email='therapist2@example.com',
            password='pass12345', role='therapist',
        )
        self.other_therapist_profile = TherapistProfile.objects.create(user=self.other_therapist_user)

        self.patient_user = User.objects.create_user(
            username='patient1', email='patient1@example.com',
            password='pass12345', role='patient',
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user, therapist=self.therapist_profile,
        )

    def test_owning_therapist_can_unassign(self):
        self.client.force_login(self.therapist_user)
        url = reverse('therapist_portal:unassign_patient', args=[self.patient_profile.id])

        response = self.client.post(url)

        self.patient_profile.refresh_from_db()
        self.assertIsNone(self.patient_profile.therapist)
        self.assertRedirects(response, reverse('therapist_dashboard'), fetch_redirect_response=False)

    def test_non_owning_therapist_cannot_unassign(self):
        self.client.force_login(self.other_therapist_user)
        url = reverse('therapist_portal:unassign_patient', args=[self.patient_profile.id])

        self.client.post(url)

        self.patient_profile.refresh_from_db()
        self.assertEqual(self.patient_profile.therapist, self.therapist_profile)

    def test_unassign_requires_post(self):
        self.client.force_login(self.therapist_user)
        url = reverse('therapist_portal:unassign_patient', args=[self.patient_profile.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)
        self.patient_profile.refresh_from_db()
        self.assertEqual(self.patient_profile.therapist, self.therapist_profile)
