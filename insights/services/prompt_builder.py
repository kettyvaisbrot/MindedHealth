from datetime import datetime

def build_insight_prompt(logs, metrics=None, correlations=None):
    prompt = ""

    # 1️⃣ Key metrics
    if metrics:
        prompt += (
            "🌟 Here are your key achievements for the past 7 days:\n"
            f"- 🧠 Medication adherence: {metrics['medication_adherence_percent']}%\n"
            f"- 💊 Missed doses: {metrics['missed_doses']}\n"
            f"- 🛌 Average sleep: {metrics['avg_sleep_hours']} hours\n"
            f"- 🌙 Nights waking up: {metrics['nights_awakened']}\n"
            f"- 🏃‍♂️ Days exercised: {metrics['days_exercised']}\n"
            f"- 🍽 Skipped meals: {metrics['skipped_meals']}\n"
            f"- Felt off events: {metrics['felt_off_count']} (avg intensity: {metrics['avg_felt_off_intensity']})\n"
            f"- 👥 Avg meeting positivity: {metrics['avg_meeting_positivity']}, positive meetings: {metrics['positive_meetings']}\n\n"
        )

    # 2️⃣ Correlations
    if correlations:
        prompt += "🔍 Identified patterns and correlations:\n"
        prompt += correlations + "\n\n"

    # 3️⃣ Structured logs
    prompt += "Here is your activity log for the past 7 days:\n\n"
    for log in logs.get("food", []):
        prompt += f"- 🍽 Food on {log.date}: Breakfast={log.breakfast_ate}, Lunch={log.lunch_ate}, Dinner={log.dinner_ate}\n"
    for log in logs.get("sport", []):
        prompt += f"- 🏃‍♂️ Sport on {log.date}: Did sport={log.did_sport}, Type={log.sport_type or log.other_sport}\n"
    for log in logs.get("sleep", []):
        prompt += f"- 🛌 Sleep on {log.date}: Slept at {log.went_to_sleep_yesterday}, Woke up at {log.wake_up_time}, Woke up during night={log.woke_up_during_night}\n"
    for log in logs.get("meetings", []):
        prompt += f"- 👥 Meetings on {log.date} at {log.time}: Type={log.meeting_type}, Positivity rating={log.positivity_rating}\n"
    for log in logs.get("felt_off", []):
        if log.had_moment:
            prompt += (
                f"- Felt Off on {log.date}: Duration={log.duration or 'N/A'}, "
                f"Intensity={log.intensity or 'N/A'}, Description='{log.description or 'No details provided'}'\n"
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
