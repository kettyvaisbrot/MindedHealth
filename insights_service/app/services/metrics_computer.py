def compute_metrics(logs: dict) -> dict:
    metrics = {}

    # Sleep
    sleep_logs = logs.get("sleep", [])
    sleep_hours = [l.get("hours") for l in sleep_logs if l.get("hours") is not None]
    metrics["avg_sleep_hours"] = round(sum(sleep_hours)/len(sleep_hours), 1) if sleep_hours else 0
    metrics["nights_awakened"] = sum(1 for l in sleep_logs if l.get("woke_up_during_night"))

    # Medications
    med_logs = logs.get("medications", [])
    metrics["missed_doses"] = sum(1 for l in med_logs if not l.get("taken"))
    metrics["taken_doses"] = sum(1 for l in med_logs if l.get("taken"))

    # Sport
    metrics["days_exercised"] = sum(1 for l in logs.get("sport", []) if l.get("did_sport"))

    # Food
    metrics["skipped_meals"] = sum(
        1 for l in logs.get("food", [])
        if not (l.get("breakfast_ate") and l.get("lunch_ate") and l.get("dinner_ate"))
    )

    # Felt off
    felt_off = [l for l in logs.get("felt_off", []) if l.get("had_moment")]
    metrics["felt_off_count"] = len(felt_off)
    metrics["avg_felt_off_intensity"] = (
        round(sum(l.get("intensity", 0) for l in felt_off) / len(felt_off), 1)
        if felt_off else 0
    )

    # Medication adherence percent (derived from already-computed dose counts)
    total_doses = metrics["taken_doses"] + metrics["missed_doses"]
    metrics["medication_adherence_percent"] = (
        round(metrics["taken_doses"] / total_doses * 100, 1) if total_doses else 0
    )

    # Meetings
    meeting_logs = logs.get("meetings", [])
    positivity_scores = [
        l.get("positivity_rating")
        for l in meeting_logs
        if l.get("positivity_rating") is not None
    ]
    metrics["avg_meeting_positivity"] = (
        round(sum(positivity_scores) / len(positivity_scores), 1) if positivity_scores else 0
    )
    metrics["positive_meetings"] = sum(1 for s in positivity_scores if s >= 3)

    return metrics


def compute_correlations(logs: dict, metrics: dict) -> str:
    messages = []

    if metrics["missed_doses"] > 0 and metrics["felt_off_count"] > 0:
        messages.append(
            f"You missed {metrics['missed_doses']} medication doses and reported feeling off "
            f"{metrics['felt_off_count']} times. There may be a connection."
        )

    if metrics["avg_sleep_hours"] < 6:
        messages.append(
            f"Average sleep was {metrics['avg_sleep_hours']} hours. Short sleep may affect mood or energy."
        )

    if metrics["days_exercised"] < 3:
        messages.append(
            f"Exercised {metrics['days_exercised']} days. Low activity may impact energy and mood."
        )

    return "\n".join(messages) if messages else "No significant correlations detected."
