# insights/services/metrics_computer.py
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import base64


# -------------------- Metrics Computation -------------------- #
def compute_metrics(logs):
    metrics = {}

    # --- Medications (detailed per med) ---
    med_logs = logs.get("medications", [])
    medication_summary = {}  # {med_name: {times_per_day, total_scheduled, taken, missed_dates, late_or_early}}

    if med_logs:
        # determine period based on logs
        start_date = min(log.date for log in med_logs)
        end_date = max(log.date for log in med_logs)
        days_in_period = (end_date - start_date).days + 1
    else:
        days_in_period = 0

    for log in med_logs:
        med = log.medication
        med_name = med.name
        if med_name not in medication_summary:
            medication_summary[med_name] = {
                "times_per_day": med.times_per_day,
                "total_scheduled": med.times_per_day * days_in_period,
                "taken": 0,
                "missed_dates": [],
                "late_or_early": [],
            }

        if getattr(log, "time_taken", None):
            medication_summary[med_name]["taken"] += 1

            # Calculate delay if dose_times exist
            scheduled_times = med.dose_times or []
            if log.dose_index < len(scheduled_times):
                scheduled_str = scheduled_times[log.dose_index]
                scheduled_time = datetime.strptime(scheduled_str, "%H:%M").time()
                actual_time = log.time_taken
                diff_hours = (datetime.combine(datetime.today(), actual_time) -
                              datetime.combine(datetime.today(), scheduled_time)).total_seconds() / 3600
                if abs(diff_hours) >= 0.5:
                    medication_summary[med_name]["late_or_early"].append({
                        "date": log.date,
                        "hours_diff": round(diff_hours, 1),
                        "late": diff_hours > 0
                    })
        else:
            medication_summary[med_name]["missed_dates"].append(log.date)

    # Overall adherence %
    total_doses = sum(v["total_scheduled"] for v in medication_summary.values())
    total_taken = sum(v["taken"] for v in medication_summary.values())
    metrics["medication_details"] = medication_summary
    metrics["medication_adherence_percent"] = round((total_taken / total_doses) * 100, 1) if total_doses else 0
    metrics["missed_doses"] = total_doses - total_taken

    # --- Sleep ---
    sleep_durations = []
    for log in logs.get("sleep", []):
        hours = getattr(log, "get_sleep_hours", lambda: None)()
        if hours is not None:
            sleep_durations.append(hours)
    metrics["avg_sleep_hours"] = round(sum(sleep_durations)/len(sleep_durations), 1) if sleep_durations else 0
    metrics["nights_awakened"] = sum(1 for log in logs.get("sleep", []) if getattr(log, "woke_up_during_night", False))

    # --- Sport ---
    metrics["days_exercised"] = sum(1 for log in logs.get("sport", []) if getattr(log, "did_sport", False))

    # --- Food ---
    metrics["skipped_meals"] = sum(
        1 for log in logs.get("food", []) if not (getattr(log, "breakfast_ate", False) and
                                                  getattr(log, "lunch_ate", False) and
                                                  getattr(log, "dinner_ate", False))
    )

    # --- Felt Off ---
    felt_off_events = [log for log in logs.get("felt_off", []) if getattr(log, "had_moment", False)]
    metrics["felt_off_count"] = len(felt_off_events)
    metrics["avg_felt_off_intensity"] = round(
        sum(getattr(log, "intensity", 0) for log in felt_off_events)/len(felt_off_events), 1
    ) if felt_off_events else 0

    # --- Meetings ---
    positivity_scores = [getattr(log, "positivity_rating", None) for log in logs.get("meetings", []) if getattr(log, "positivity_rating", None) is not None]
    metrics["avg_meeting_positivity"] = round(sum(positivity_scores)/len(positivity_scores), 1) if positivity_scores else 0
    metrics["positive_meetings"] = sum(1 for score in positivity_scores if score >= 3)

    return metrics


# -------------------- Correlations -------------------- #
def compute_correlations(logs, metrics):
    correlations_summary = []

    # Missed meds → Felt off
    if metrics.get("missed_doses", 0) > 0 and metrics.get("felt_off_count", 0) > 0:
        correlations_summary.append(
            f"- You missed {metrics['missed_doses']} medication doses and reported feeling off {metrics['felt_off_count']} times. There may be a connection."
        )

    # Sleep → Felt off / activity
    avg_sleep = metrics.get("avg_sleep_hours", 0)
    nights_awakened = metrics.get("nights_awakened", 0)
    days_exercised = metrics.get("days_exercised", 0)

    if avg_sleep < 6:
        correlations_summary.append(f"- Average sleep was {avg_sleep} hours. Short sleep may affect mood or energy.")
    if nights_awakened >= 2:
        correlations_summary.append(f"- Woke up {nights_awakened} nights. Interrupted sleep can influence mood and alertness.")
    if days_exercised < 3:
        correlations_summary.append(f"- Exercised {days_exercised} days. Low activity may impact energy and mood.")

    # Skipped meals → Mood dips
    skipped_meals = metrics.get("skipped_meals", 0)
    if skipped_meals > 0:
        correlations_summary.append(f"- Skipped meals on {skipped_meals} days. This may affect energy and mood.")

    return "\n".join(correlations_summary) if correlations_summary else "- No significant correlations detected this week."

# -------------------- Positive Trends -------------------- #
def get_positive_trends(logs):
    trends = {}

    # Sleep
    sleep_dates, sleep_hours = [], []
    for log in logs.get("sleep", []):
        hours = getattr(log, "get_sleep_hours", lambda: None)()
        if hours:
            sleep_dates.append(log.date)
            sleep_hours.append(hours)
    trends["sleep"] = (sleep_dates, sleep_hours, 6)

    # Medications (dose taken)
    med_dates, med_taken = [], []
    for log in logs.get("medications", []):
        med_dates.append(log.date)
        med_taken.append(1 if getattr(log, "time_taken", None) else 0)
    trends["medication"] = (med_dates, med_taken, 1)

    return trends

    # --- Medications chart ---
    med_details = metrics.get("medication_details", {})
    for med_name, info in med_details.items():
        if info["total_scheduled"] == 0:
            continue

        taken_days = [d.strftime("%Y-%m-%d") for d in info.get("taken_dates", [])]
        missed_days = [d.strftime("%Y-%m-%d") for d in info.get("missed_days", [])]

        fig, ax = plt.subplots()
        ax.bar(taken_days, [1]*len(taken_days), color="#43a047", label="Taken")
        if missed_days:
            ax.bar(missed_days, [1]*len(missed_days), color="#e53935", label="Missed")
        ax.set_ylim(0, 1.5)
        ax.set_ylabel("Dose taken")
        ax.set_title(f"💊 {med_name} Dose Tracking")
        ax.legend()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches='tight')
        plt.close(fig)
        charts[f"{med_name}_chart"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    return charts


# -------------------- Format Medications for AI -------------------- #
def format_medication_insights(med_summary):
    messages = []
    for med, info in med_summary.items():
        msg = f"**{med}**: "
        if info["missed_dates"]:
            missed_str = ", ".join(str(d) for d in info["missed_dates"])
            msg += f"Missed on {missed_str}. "
        if info["delays"]:
            delays_str = ", ".join(f"{d['date']} ({d['delay_minutes']} min late)" for d in info["delays"])
            msg += f"Taken late on {delays_str}. "
        if not info["missed_dates"] and not info["delays"]:
            msg += "Taken as scheduled every day. ✅"
        messages.append(msg)
    return "\n".join(messages)
