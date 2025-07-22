def build_insight_prompt(logs):
    prompt = (
        "The following is the user's activity and medication log for the past 7 days:\n\n"
        "Based on this structured mental health data, provide a clear and compassionate insight for the user.\n"
        "Speak directly to the user using second person (e.g., 'I see you took...', 'You skipped...').\n"
        "Use simple language that’s easy to understand.\n"
        "Organize the insight using the following sections:\n\n"
        "- 🧠 Medication Review\n"
        "- 🔁 Behavioral Patterns\n"
        "- 📊 Trends or Risks\n"
        "- 💡 Gentle Suggestions\n\n"
        "Here is the structured log data:\n\n"
    )

    for log in logs["food"]:
        prompt += f"- Food on {log.date}: Breakfast={log.breakfast_ate}, Lunch={log.lunch_ate}, Dinner={log.dinner_ate}\n"
    for log in logs["sport"]:
        prompt += f"- Sport on {log.date}: Did sport={log.did_sport}, Type={log.sport_type or log.other_sport}\n"
    for log in logs["sleep"]:
        prompt += f"- Sleep on {log.date}: Slept at {log.went_to_sleep_yesterday}, Woke up at {log.wake_up_time}, Woke up during night={log.woke_up_during_night}\n"
    for log in logs["meetings"]:
        prompt += f"- Meetings on {log.date} at {log.time}: Type={log.meeting_type}, Positivity rating={log.positivity_rating}\n"
    for log in logs["felt_off"]:
        if log.had_moment:
            prompt += (
                f"- Felt Off on {log.date}: Duration={log.duration or 'N/A'}, "
                f"Intensity={log.intensity or 'N/A'}, Description='{log.description or 'No details provided'}'\n"
            )
    for log in logs["medications"]:
        med = log.medication
        prompt += f"- Medication on {log.date}: Took {med.name} ({med.dose}) at {log.time_taken} [dose #{log.dose_index + 1} of {med.times_per_day}]\n"

    prompt += (
        "\n\n---\n\n"
        "Imagine you are a compassionate psychiatrist reviewing this patient's logs. Your goal is to provide a professional, empathetic, and clear mental health insight.\n"
        "Write directly to the user using second-person language (e.g., 'I notice you...', 'You might consider...').\n"
        "Begin by acknowledging the effort they put into tracking their health.\n"
        "Then, in each section, carefully identify specific patterns and behaviors found in the logs, especially regarding medication timing and adherence.\n"
        "Gently but clearly point out any missed or delayed medication doses and discuss possible impacts on mood or wellbeing.\n"
        "Highlight behavioral patterns related to sleep, activity, meals, and social interactions, noting any trends that may affect mental health.\n"
        "Conclude each section with compassionate, actionable suggestions for improvement — phrased as invitations or encouragements, never criticism.\n"
        "Use clear section headings:\n"
        "🧠 Medication Review\n"
        "🔁 Behavioral Patterns\n"
        "📊 Identified Patterns and Triggers\n"
        "💡 Recommendations\n"
        "Avoid vague platitudes. Focus on thoughtful, specific, and kind observations and advice that help the user understand their data and make positive changes if they wish.\n"
    )

    return prompt
