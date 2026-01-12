from datetime import datetime
def v(obj, key, default="N/A"):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def build_insight_prompt(logs, metrics=None, correlations=None):
    prompt = ""

    # 1️⃣ Key metrics
    if metrics:
        prompt += (
            "🌟 Here are your key achievements for the past 7 days:\n"
            f"- 🧠 Medication adherence: {metrics.get('medication_adherence_percent', 'N/A')}%\n"
            f"- 💊 Missed doses: {metrics.get('missed_doses')}\n"
            f"- 🛌 Average sleep: {metrics.get('avg_sleep_hours')} hours\n"
            f"- 🌙 Nights waking up: {metrics.get('nights_awakened')}\n"
            f"- 🏃‍♂️ Days exercised: {metrics.get('days_exercised')}\n"
            f"- 🍽 Skipped meals: {metrics.get('skipped_meals')}\n"
            f"- Felt off events: {metrics.get('felt_off_count')} (avg intensity: {metrics.get('avg_felt_off_intensity')})\n"
            f"- 👥 Avg meeting positivity: {metrics.get('avg_meeting_positivity')}, positive meetings: {metrics.get('positive_meetings')}\n\n"
        )

    # 2️⃣ Correlations
    if correlations:
        prompt += "🔍 Identified patterns and correlations:\n"
        prompt += correlations + "\n\n"

    # 3️⃣ Structured logs
    prompt += "Here is your activity log for the past 7 days:\n\n"

    def log_day(x):
        # support both 'date' and 'created_at' shapes
        return v(x, "date", v(x, "created_at"))

    for log in logs.get("food", []):
        prompt += (
            f"- 🍽 Food on {log_day(log)}: "
            f"Breakfast={v(log, 'breakfast_ate')}, "
            f"Lunch={v(log, 'lunch_ate')}, "
            f"Dinner={v(log, 'dinner_ate')}\n"
        )

    for log in logs.get("sport", []):
        sport_type = v(log, "sport_type", "")
        other_sport = v(log, "other_sport", "")
        prompt += (
            f"- 🏃‍♂️ Sport on {log_day(log)}: "
            f"Did sport={v(log, 'did_sport')}, "
            f"Type={sport_type or other_sport or 'N/A'}\n"
        )

    for log in logs.get("sleep", []):
        prompt += (
            f"- 🛌 Sleep on {log_day(log)}: "
            f"Slept at {v(log, 'went_to_sleep_yesterday')}, "
            f"Woke up at {v(log, 'wake_up_time')}, "
            f"Woke up during night={v(log, 'woke_up_during_night')}\n"
        )

    for log in logs.get("meetings", []):
        prompt += (
            f"- 👥 Meetings on {log_day(log)} at {v(log, 'time')}: "
            f"Type={v(log, 'meeting_type')}, "
            f"Positivity rating={v(log, 'positivity_rating')}\n"
        )

    for log in logs.get("felt_off", []):
        if v(log, "had_moment", False):
            duration = v(log, "duration")
            intensity = v(log, "intensity")
            description = v(log, "description", "No details provided")
            prompt += (
                f"- Felt Off on {log_day(log)}: "
                f"Duration={duration}, Intensity={intensity}, Description='{description}'\n"
            )


    # 4️⃣ Medications summary (explicit names, no rephrasing)
    prompt += "\n🧠 Medication Review\n"
    if metrics and "medication_details" in metrics:
        # Medications taken at least once
        taken_meds = [name for name, info in metrics["medication_details"].items() if info["taken"] > 0]
        if taken_meds:
            meds_str = ", ".join(taken_meds)
            total_taken = sum(info["taken"] for info in metrics["medication_details"].values())
            total_scheduled = sum(info["total_scheduled"] for info in metrics["medication_details"].values())
            prompt += (
                f"I notice you managed to take the following medications this week: {meds_str} "
                f"({total_taken} out of {total_scheduled} scheduled doses). "
                "Do NOT rephrase the medication names; always keep them exactly as listed. "
                "It's important to keep working on this, so keep aiming for that streak! "
                "Every step counts towards your wellness journey 💊\n"
            )
        else:
            prompt += (
                "It looks like you didn’t take any of your scheduled doses this week. "
                "Let's try to improve your routine next week 💊\n"
            )

        # Detailed doses per medication
        for med_name, info in metrics["medication_details"].items():
            msg = f"- 💊 {med_name}: Taken {info['taken']} out of {info['total_scheduled']} scheduled doses"
            if info["missed_dates"]:
                missed_str = ", ".join(str(d) for d in info["missed_dates"])
                msg += f"; Missed on {missed_str}"
            if info["late_or_early"]:
                delays_str = ", ".join(
                    f"{d['date']} ({d['hours_diff']}h {'late' if d['late'] else 'early'})" 
                    for d in info["late_or_early"]
                )
                msg += f"; Taken off schedule on {delays_str}"
            prompt += msg + "\n"

    # 5️⃣ Positive trends text
    prompt += "\n📊 Positive Trends and Observations\n"
    if metrics:
        # Sleep trend
        avg_sleep = metrics.get("avg_sleep_hours", 0)
        if avg_sleep >= 7:
            prompt += f"- 🛌 You averaged {avg_sleep} hours of sleep. Great job maintaining rest!\n"
        elif avg_sleep > 0:
            prompt += f"- 🛌 You averaged {avg_sleep} hours of sleep. Consider improving your sleep schedule.\n"

        # Exercise trend
        days_exercised = metrics.get("days_exercised", 0)
        if days_exercised >= 3:
            prompt += f"- 🏃‍♂️ You exercised {days_exercised} days. Keep up the active lifestyle!\n"
        else:
            prompt += f"- 🏃‍♂️ You exercised {days_exercised} days. Try to stay more active.\n"

        # Meals
        skipped_meals = metrics.get("skipped_meals", 0)
        if skipped_meals > 0:
            prompt += f"- 🍽 You skipped meals on {skipped_meals} days. Try to maintain regular meals.\n"

        # Felt off
        felt_off_count = metrics.get("felt_off_count", 0)
        if felt_off_count > 0:
            prompt += f"- You had {felt_off_count} moments of feeling off. Consider tracking triggers.\n"

    # 6️⃣ Instructions for AI
    prompt += "\n---\n\n"
    prompt += (
        "Imagine you are a compassionate mental health assistant. "
        "Your goal is to provide clear, friendly, and motivating insights to the user. "
        "Use second-person language (e.g., 'I notice you...', 'You did a great job...'). "
        "Do NOT rephrase the names of medications; always keep them exactly as listed. "
        "Highlight positive trends and achievements such as consistent sleep, medication adherence, exercise, or positive meetings. "
        "Use short, clear, uplifting sentences and celebrate small wins.\n"
    )

    return prompt
