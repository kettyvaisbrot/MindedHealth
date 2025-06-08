from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import openai

from dashboard.models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog

from medications.models import MedicationLog

openai.api_key = settings.OPENAI_API_KEY


@login_required
def ai_insights_view(request):
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # Collect logs for the last 7 days
    food_logs = FoodLog.objects.filter(user=user, date__range=(week_ago, today))
    sport_logs = SportLog.objects.filter(user=user, date__range=(week_ago, today))
    sleep_logs = SleepingLog.objects.filter(user=user, date__range=(week_ago, today))
    meetings_logs = Meetings.objects.filter(user=user, date__range=(week_ago, today))
    seizure_logs = SeizureLog.objects.filter(user=user, date__range=(week_ago, today))
    med_logs = MedicationLog.objects.filter(
        user=user, date__range=(week_ago, today)
    ).select_related("medication")

    # Check if user has at least one log
    if not any(
        [
            food_logs.exists(),
            sport_logs.exists(),
            sleep_logs.exists(),
            meetings_logs.exists(),
            seizure_logs.exists(),
            med_logs.exists(),
        ]
    ):
        message = "😊 It’s time to get to know each other! Start documenting your day-to-day life via the dashboard."
        return render(request, "insights/insights.html", {"insights": message})

    # Start building prompt
    prompt = "The following is the user's activity and medication log for the past 7 days:\n\n"

    for log in food_logs:
        prompt += f"- Food on {log.date}: Breakfast={log.breakfast_ate}, Lunch={log.lunch_ate}, Dinner={log.dinner_ate}\n"
    for log in sport_logs:
        prompt += f"- Sport on {log.date}: Did sport={log.did_sport}, Type={log.sport_type or log.other_sport}\n"
    for log in sleep_logs:
        prompt += f"- Sleep on {log.date}: Slept at {log.went_to_sleep_yesterday}, Woke up at {log.wake_up_time}, Woke up during night={log.woke_up_during_night}\n"
    for log in meetings_logs:
        prompt += f"- Meetings on {log.date} at {log.time}: Type={log.meeting_type}, Positivity rating={log.positivity_rating}\n"
    for log in seizure_logs:
        prompt += f"- Seizure on {log.date} at {log.time}: Duration {log.duration_minutes} minutes\n"
    for log in med_logs:
        med = log.medication
        prompt += f"- Medication on {log.date}: Took {med.name} ({med.dose}) at {log.time_taken} [dose #{log.dose_index + 1} of {med.times_per_day}]\n"

    prompt += (
        "\nBased on this activity and medication data, generate a short, kind, emotionally supportive insight or recommendation "
        "to improve the user's mental well-being. Avoid criticism, be gentle and encouraging. Include references to how medication adherence or timing may affect mental health if relevant."
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a compassionate mental health assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        ai_response = response.choices[0].message.content.strip()

    except Exception as e:
        ai_response = f"Something went wrong while generating insights. ({str(e)})"

    return render(request, "insights/insights.html", {"insights": ai_response})
