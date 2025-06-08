import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import (
    FoodLog,
    SportLog,
    SleepingLog,
    Meetings,
    MeetingType,
    SeizureLog,
    Medication,
    MedicationLog,
)


class Command(BaseCommand):
    help = "Generate mock data for testing"

    def handle(self, *args, **kwargs):
        user = User.objects.first()

        if not user:
            user = User.objects.create_user(username="testuser", password="testpass")

        today = datetime.today().date()

        # Create predefined meeting types if they don't exist
        meeting_types = ["family", "friends", "business", "strangers"]
        for mt in meeting_types:
            MeetingType.objects.get_or_create(name=mt)

        # Generate FoodLog mock data
        meals = ["breakfast", "lunch", "dinner"]
        for i in range(10):
            FoodLog.objects.create(
                user=user,
                date=today - timedelta(days=i),
                meal=random.choice(meals),
                ate=random.choice([True, False]),
                time=(datetime.now() - timedelta(hours=random.randint(1, 24))).time(),
            )

        # Generate SportLog mock data
        sports = ["swimming", "running", "walking", "gym", "other"]
        for i in range(10):
            SportLog.objects.create(
                user=user,
                date=today - timedelta(days=i),
                did_sport=random.choice([True, False]),
                sport_type=random.choice(sports),
                other_sport="Yoga" if random.choice([True, False]) else "",
            )

        # Generate SleepingLog mock data
        for i in range(10):
            SleepingLog.objects.create(
                user=user,
                date=today - timedelta(days=i),
                sleep_time=(
                    datetime.now() - timedelta(hours=random.randint(1, 24))
                ).time(),
                wake_time=(
                    datetime.now() - timedelta(hours=random.randint(1, 24))
                ).time(),
                woke_up_during_night=random.choice([True, False]),
            )

        # Generate Meetings mock data
        meeting_types_objs = list(MeetingType.objects.all())
        for i in range(10):
            meeting = Meetings.objects.create(
                date=today - timedelta(days=i),
                time=(datetime.now() - timedelta(hours=random.randint(1, 24))).time(),
                met_people=random.choice([True, False]),
                positivity_rating=random.randint(1, 5),
            )
            if meeting_types_objs:
                meeting.meeting_types.add(random.choice(meeting_types_objs))

        # Generate SeizureLog mock data
        for i in range(10):
            SeizureLog.objects.create(
                user=user,
                seizure_time=datetime.now()
                - timedelta(days=i, hours=random.randint(1, 24)),
                duration_minutes=random.randint(1, 60),
                last_memory="Last thing I remember...",
            )

        # Generate Medication mock data
        medication_names = ["MedA", "MedB", "MedC"]
        medications = []
        for name in medication_names:
            med = Medication.objects.create(
                user=user,
                name=name,
                daily_dose="1 pill",
                times_per_day=random.randint(1, 3),
            )
            medications.append(med)

        # Generate MedicationLog mock data
        for med in medications:
            for i in range(10):
                MedicationLog.objects.create(
                    medication=med,
                    date=today - timedelta(days=i),
                    time_taken=(
                        datetime.now() - timedelta(hours=random.randint(1, 24))
                    ).time(),
                    feeling_after_half_hour=random.choice(["Good", "Okay", "Bad"]),
                    feeling_after_one_hour=random.choice(["Good", "Okay", "Bad"]),
                )
