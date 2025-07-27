from datetime import datetime, date, time
from django.utils.timezone import localtime
from medications.models import MedicationLog, Medication
from dashboard.models import FeltOffLog

def get_medication_questions(user):
    today = date.today()

    # 🧪 Check if the user already logged any medication today
    if MedicationLog.objects.filter(user=user, date=today).exists():
        questions = [
            {
                "field": "meds_already_logged",
                "question": "👋 Hi again! You already documented your medications today.",
                "type": "select",
                "options": ["📝 Update my log", "⬅️ Back to Dashboard"]
            },
            {
                "field": "continue_update",
                "question": "Please update your medications below:",
                "type": "info",
                "condition": {
                    "field": "meds_already_logged",
                    "value": "📝 Update my log"
                }
            }
        ]

        # Show ALL meds and ALL scheduled doses
        meds = Medication.objects.filter(user=user)
        for med in meds:
            raw_times = med.dose_times

            dose_times = (
                raw_times if isinstance(raw_times, list)
                else [t.strip() for t in raw_times.split(",")]
            )

            for idx, t in enumerate(dose_times):
                try:
                    dose_time = datetime.strptime(t, "%H:%M").time()
                except ValueError:
                    continue

                prefix = f"{med.id}_{idx}"

                questions.append({
                    "field": f"took_{prefix}",
                    "question": f"💊 Did you take {med.name} (scheduled at {dose_time})?",
                    "type": "select",
                    "options": ["yes", "no"],
                    "condition": {
                        "field": "meds_already_logged",
                        "value": "📝 Update my log"
                    }
                })

                questions.append({
                    "field": f"time_{prefix}",
                    "question": f"⏰ What time did you take {med.name}?",
                    "type": "time",
                    "condition": {
                        "field": f"took_{prefix}",
                        "value": "yes"
                    }
                })

        return questions

    # If no medication was logged yet today, continue with time-block logic
    now = localtime().time()

    time_blocks = [
        ("morning", time(6, 0), time(12, 0)),
        ("lunch", time(12, 0), time(17, 0)),
        ("evening", time(17, 0), time(23, 59)),
    ]

    block_name, start, end = None, None, None
    for name, s, e in time_blocks:
        if s <= now <= e:
            block_name, start, end = name, s, e
            break

    if not block_name:
        return [{
            "field": "no_meds_now",
            "question": "🎉 You have no medications to take right now.",
            "type": "info"
        }]

    meds = Medication.objects.filter(user=user)
    relevant_meds = []

    for med in meds:
        raw_times = med.dose_times
        dose_times = (
            raw_times if isinstance(raw_times, list)
            else [t.strip() for t in raw_times.split(",")]
        )

        for idx, t in enumerate(dose_times):
            try:
                dose_time = datetime.strptime(t, "%H:%M").time()
            except ValueError:
                continue

            if start <= dose_time <= end:
                relevant_meds.append((med, idx, t))

    if not relevant_meds:
        return [{
            "field": "no_meds_now",
            "question": "🎉 You have no medications to take right now.",
            "type": "info"
        }]

    # Build the main chat questions for current time block
    questions = [{
        "field": f"took_{block_name}_meds",
        "question": f"💊 Did you take your {block_name} medications?",
        "type": "select",
        "options": ["yes", "no"]
    }]

    for med, idx, dose_time in relevant_meds:
        prefix = f"{med.id}_{idx}"

        questions.append({
            "field": f"took_{prefix}",
            "question": f"✅ Did you take {med.name} (scheduled at {dose_time})?",
            "type": "select",
            "options": ["yes", "no"],
            "condition": {
                "field": f"took_{block_name}_meds",
                "value": "yes"
            }
        })

        questions.append({
            "field": f"time_{prefix}",
            "question": f"⏰ What time did you take {med.name}?",
            "type": "time",
            "condition": {
                "field": f"took_{prefix}",
                "value": "yes"
            }
        })

    # Encouragement if user said no to all
    questions.append({
        "field": "encouragement",
        "question": "🧠 It's okay if you forgot. Try to take them now. You're doing your best ❤️",
        "type": "info",
        "condition": {
            "field": f"took_{block_name}_meds",
            "value": "no"
        }
    })

    return questions

def get_felt_off_questions(user):
    return [
        {
            "field": "had_moment",
            "question": "💭 Did you experience a moment that felt off today?",
            "type": "select",
            "options": ["yes", "no"],
            "next_if": {
                "yes": 1,  # Go to index 1 if user says "yes"
                "no": "end"    # Skip to the end if user says "no"
            }
        },
        {
            "field": "duration",
            "question": "⏱️ How long did it last?",
            "type": "text"
        },
        {
            "field": "intensity",
            "question": "📶 How intense was it (1-5)?",
            "type": "select",
            "options": [str(i) for i in range(1, 6)]
        },
        {
            "field": "description",
            "question": "📝 Can you describe what you felt?",
            "type": "textarea"
        }
    ]