from django.test import TestCase, Client
from users.models import User, TherapistProfile, PatientProfile, FamilyMemberProfile
from django.urls import reverse

class UsersModelsTest(TestCase):
    def setUp(self):
        self.therapist_user = User.objects.create_user(
            username='therapist2', password='testpass', role='therapist'
        )
        self.therapist_profile = TherapistProfile.objects.create(
            user=self.therapist_user,
            specialization='Psychology',
            license_number='LIC12345'
        )

        self.patient_user = User.objects.create_user(
            username='patient2', password='testpass', role='patient'
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            therapist=self.therapist_profile
        )
        print(self.patient_profile.id)

        self.family_user = User.objects.create_user(
            username='family2', password='testpass', role='family'
        )
        self.family_profile = FamilyMemberProfile.objects.create(
            user=self.family_user,
            related_patient=self.patient_profile,
            relation='Mother'
        )

    def test_user_roles(self):
        self.assertEqual(self.therapist_user.role, 'therapist')
        self.assertEqual(self.patient_user.role, 'patient')
        self.assertEqual(self.family_user.role, 'family')

    def test_therapist_profile_str(self):
        self.assertEqual(str(self.therapist_profile), "therapist2 (Psychology)")

    def test_patient_profile_str(self):
        self.assertEqual(str(self.patient_profile), "patient2 (Therapist: therapist2)")

    def test_family_profile_str(self):
        self.assertEqual(str(self.family_profile), "family2 -> patient2")

    def test_patient_therapist_relationship(self):
        self.assertEqual(self.patient_profile.therapist, self.therapist_profile)
        self.assertIn(self.patient_profile, self.therapist_profile.patients.all())

    def test_family_patient_relationship(self):
        self.assertEqual(self.family_profile.related_patient, self.patient_profile)
        self.assertEqual(self.patient_profile.family_member, self.family_profile)

class UsersViewsTest(TestCase):
    def setUp(self):
        self.therapist_user = User.objects.create_user(
            username='therapist1', password='pass', role='therapist'
        )
        self.therapist_profile = TherapistProfile.objects.create(
            user=self.therapist_user,
            specialization='Psychologist',
            license_number='12345'
        )
        self.patient_user = User.objects.create_user(
            username='patient1', password='pass', role='patient'
        )

        self.patient_user.save()

        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            therapist=self.therapist_profile
        )
        self.patient_profile.save()

    def test_therapist_dashboard_access(self):
        self.client.login(username='therapist1', password='pass')
        response = self.client.get(reverse('therapist_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'therapist1')

    def test_family_dashboard_access(self):
        self.client.login(username='family1', password='pass')
        response = self.client.get(reverse('family_dashboard', args=[self.family_profile.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'family1')
        self.assertContains(response, 'patient1')

    def test_patient_detail_view(self):
        self.client.force_login(self.therapist_user) 
        patient_id = self.patient_profile.id
        self.assertIsNotNone(patient_id)

        url = reverse('patient_detail', args=[patient_id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patient_user.username)
