from datetime import date, timedelta

from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from dashboard.models import FoodLog, MedicationIntakeLog, SeizureLog
from medications.models import Medication
from therapist_portal.models import PatientAlert
from therapist_portal.utils import get_last_activity_by_user
from therapist_portal.views import patient_documentation
from users.models import PatientProfile, TherapistProfile, User
from users.views import therapist_dashboard


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


class GetLastActivityByUserTests(TestCase):
    """Unit tests for the helper itself — no HTTP, no login involved."""

    def setUp(self):
        self.user_a = User.objects.create_user(
            username='activity_a', email='activity_a@example.com',
            password='pass12345', role='patient',
        )
        self.user_b = User.objects.create_user(
            username='activity_b', email='activity_b@example.com',
            password='pass12345', role='patient',
        )

    def test_takes_max_across_multiple_models(self):
        older = date.today() - timedelta(days=10)
        newer = date.today() - timedelta(days=3)
        FoodLog.objects.create(user=self.user_a, date=older)
        SeizureLog.objects.create(user=self.user_a, date=newer, duration_minutes=2)

        result = get_last_activity_by_user([self.user_a.id])

        self.assertEqual(result[self.user_a.id], newer)

    def test_no_records_returns_none(self):
        result = get_last_activity_by_user([self.user_a.id])

        self.assertIsNone(result[self.user_a.id])

    def test_no_cross_contamination_between_patients(self):
        old_date = date.today() - timedelta(days=20)
        recent_date = date.today() - timedelta(days=1)
        FoodLog.objects.create(user=self.user_a, date=old_date)
        FoodLog.objects.create(user=self.user_b, date=recent_date)

        result = get_last_activity_by_user([self.user_a.id, self.user_b.id])

        self.assertEqual(result[self.user_a.id], old_date)
        self.assertEqual(result[self.user_b.id], recent_date)

    def test_query_count_is_constant_regardless_of_user_count(self):
        FoodLog.objects.create(user=self.user_a, date=date.today())

        with self.assertNumQueries(6):
            get_last_activity_by_user([self.user_a.id])

        # Same 6 queries whether we pass 1 id or many (extra ids are just
        # more values in the same WHERE user_id IN (...) clause).
        many_ids = [self.user_a.id, self.user_b.id] + list(range(9000, 9010))
        with self.assertNumQueries(6):
            get_last_activity_by_user(many_ids)


class TherapistDashboardLastActivityTests(TestCase):
    """Integration tests calling the view directly via RequestFactory.

    Not using self.client here: Django's test Client instruments every
    template render to build response.context, and that instrumentation
    crashes on this project's Python/Django combo (an unrelated
    RequestContext.__copy__ incompatibility — see PR #59's notes). Calling
    the view function directly with a RequestFactory request renders the
    real template through the real code path without going through that
    broken instrumentation, since it's only wired into Client.request().
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.therapist_user = User.objects.create_user(
            username='dash_therapist', email='dash_therapist@example.com',
            password='pass12345', role='therapist',
        )
        self.therapist_profile = TherapistProfile.objects.create(user=self.therapist_user)
        self.patient_user = User.objects.create_user(
            username='dash_patient', email='dash_patient@example.com',
            password='pass12345', role='patient',
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user, therapist=self.therapist_profile,
        )

    def _get_dashboard(self):
        request = self.factory.get(reverse('therapist_dashboard'))
        request.user = self.therapist_user
        return therapist_dashboard(request)

    def test_activity_today_is_not_flagged(self):
        FoodLog.objects.create(user=self.patient_user, date=date.today())

        response = self._get_dashboard()

        self.assertIn(b'0 day', response.content)
        self.assertNotIn(b'Needs attention', response.content)

    def test_exactly_5_days_is_flagged(self):
        FoodLog.objects.create(user=self.patient_user, date=date.today() - timedelta(days=5))

        response = self._get_dashboard()

        self.assertIn(b'5 days ago', response.content)
        self.assertIn(b'Needs attention', response.content)

    def test_4_days_is_not_flagged(self):
        FoodLog.objects.create(user=self.patient_user, date=date.today() - timedelta(days=4))

        response = self._get_dashboard()

        self.assertIn(b'4 days ago', response.content)
        self.assertNotIn(b'Needs attention', response.content)

    def test_no_activity_shows_new_patient_and_is_not_flagged(self):
        response = self._get_dashboard()

        self.assertIn(b'New patient', response.content)
        self.assertNotIn(b'Needs attention', response.content)

    def test_active_alert_flags_despite_recent_activity(self):
        FoodLog.objects.create(user=self.patient_user, date=date.today())
        PatientAlert.objects.create(
            user=self.patient_user, room_name='room1', reason='test', resolved=False,
        )

        response = self._get_dashboard()

        self.assertIn(b'Needs attention', response.content)

    def test_resolved_alert_does_not_flag(self):
        FoodLog.objects.create(user=self.patient_user, date=date.today())
        PatientAlert.objects.create(
            user=self.patient_user, room_name='room1', reason='test', resolved=True,
        )

        response = self._get_dashboard()

        self.assertNotIn(b'Needs attention', response.content)


class PatientDocumentationTests(TestCase):
    """Uses RequestFactory for the same reason as TherapistDashboardLastActivityTests
    above: self.client crashes on any template render in this environment."""

    def setUp(self):
        self.factory = RequestFactory()
        self.therapist_user = User.objects.create_user(
            username='doc_therapist', email='doc_therapist@example.com',
            password='pass12345', role='therapist',
        )
        self.therapist_profile = TherapistProfile.objects.create(user=self.therapist_user)

        self.other_therapist_user = User.objects.create_user(
            username='doc_other_therapist', email='doc_other_therapist@example.com',
            password='pass12345', role='therapist',
        )
        self.other_therapist_profile = TherapistProfile.objects.create(user=self.other_therapist_user)

        self.patient_user = User.objects.create_user(
            username='doc_patient', email='doc_patient@example.com',
            password='pass12345', role='patient',
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user, therapist=self.therapist_profile,
        )
        self.today = date.today()

    def _get_documentation(self, user, selected_date=None):
        url = reverse('therapist_portal:patient_documentation', args=[self.patient_profile.id])
        if selected_date:
            url += f'?date={selected_date}'
        request = self.factory.get(url)
        request.user = user
        return patient_documentation(request, self.patient_profile.id)

    def test_empty_state_when_no_documentation(self):
        response = self._get_documentation(self.therapist_user, self.today)

        self.assertIn(b'No documentation for this day', response.content)

    def test_shows_food_log_details(self):
        FoodLog.objects.create(
            user=self.patient_user, date=self.today,
            breakfast_ate=True, lunch_ate=False, dinner_ate=True,
        )

        response = self._get_documentation(self.therapist_user, self.today)

        self.assertIn(b'Breakfast: Yes', response.content)
        self.assertIn(b'Lunch: No', response.content)
        self.assertIn(b'Dinner: Yes', response.content)
        self.assertNotIn(b'No documentation for this day', response.content)

    def test_shows_seizure_log_duration(self):
        SeizureLog.objects.create(user=self.patient_user, date=self.today, duration_minutes=4)

        response = self._get_documentation(self.therapist_user, self.today)

        self.assertIn(b'Duration: 4 minutes', response.content)

    def test_shows_medication_name_not_just_id(self):
        medication = Medication.objects.create(
            name='Aspirin', times_per_day=2, dose='100mg', user=self.patient_user,
        )
        MedicationIntakeLog.objects.create(
            user=self.patient_user, medication_ref_id=medication.id,
            date=self.today, dose_index=0,
        )

        response = self._get_documentation(self.therapist_user, self.today)

        self.assertIn(b'Aspirin', response.content)

    def test_only_shows_logs_for_selected_date(self):
        other_day = self.today - timedelta(days=3)
        FoodLog.objects.create(user=self.patient_user, date=other_day, breakfast_ate=True)

        response = self._get_documentation(self.therapist_user, self.today)

        self.assertIn(b'No documentation for this day', response.content)

    def test_defaults_to_today_without_date_param(self):
        FoodLog.objects.create(user=self.patient_user, date=self.today, breakfast_ate=True)

        response = self._get_documentation(self.therapist_user, selected_date=None)

        self.assertIn(b'Breakfast: Yes', response.content)

    def test_non_owning_therapist_is_rejected(self):
        FoodLog.objects.create(user=self.patient_user, date=self.today, breakfast_ate=True)

        response = self._get_documentation(self.other_therapist_user, self.today)

        self.assertEqual(response.status_code, 302)
        self.assertNotIn(b'Breakfast', response.content)
