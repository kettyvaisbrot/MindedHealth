def build_insight_prompt(logs):
    prompt = "The following is the user's activity and medication log for the past 7 days:\n\n"

    for log in logs["food"]:
        prompt += f"- Food on {log.date}: Breakfast={log.breakfast_ate}, Lunch={log.lunch_ate}, Dinner={log.dinner_ate}\n"
    for log in logs["sport"]:
        prompt += f"- Sport on {log.date}: Did sport={log.did_sport}, Type={log.sport_type or log.other_sport}\n"
    for log in logs["sleep"]:
        prompt += f"- Sleep on {log.date}: Slept at {log.went_to_sleep_yesterday}, Woke up at {log.wake_up_time}, Woke up during night={log.woke_up_during_night}\n"
    for log in logs["meetings"]:
        prompt += f"- Meetings on {log.date} at {log.time}: Type={log.meeting_type}, Positivity rating={log.positivity_rating}\n"
    for log in logs["seizures"]:
        prompt += f"- Seizure on {log.date} at {log.time}: Duration {log.duration_minutes} minutes\n"
    for log in logs["medications"]:
        med = log.medication
        prompt += f"- Medication on {log.date}: Took {med.name} ({med.dose}) at {log.time_taken} [dose #{log.dose_index + 1} of {med.times_per_day}]\n"

    prompt += (
        "\nBased on this activity and medication data, generate a short, kind, emotionally supportive insight or recommendation "
        "to improve the user's mental well-being. Avoid criticism, be gentle and encouraging. Include references to how medication adherence or timing may affect mental health if relevant."
    )
    return prompt
