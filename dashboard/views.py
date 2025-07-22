import logging
import pprint
from django.utils.timezone import localtime, now as tz_now
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseNotFound
import datetime
import json
import requests
from medications.models import Medication
from django.utils import timezone
from django.db.models import BooleanField
from .models import FeltOffLog, FoodLog, SportLog, SleepingLog, Meetings
from django.utils.timezone import localtime as tz_localtime
from django.forms import modelform_factory
from django.contrib import messages
from datetime import datetime, time
from django.utils import timezone
from django.db import models
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated
from medications.models import MedicationLog, Medication
from medications.serializers import MedicationLogSerializer
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from dashboard.services.dashboard_service import fetch_dashboard_logs
from dashboard.utils.date_utils import parse_date_from_str
from .services.documentation_service import fetch_documentation_for_date
from .services.medication_service import log_medication_entry
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
import json
from datetime import datetime, date, time
from django.utils.timezone import localtime
from django.utils.timezone import localtime as tz_localtime



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

    # 🌅 If no medication was logged yet today, continue with time-block logic
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
                "no": 4    # Skip to the end if user says "no"
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

CATEGORY_CONFIG = {
    'felt_off': {
        "display_name": "Moments I Felt Off",
        "model": FeltOffLog,
        "questions": get_felt_off_questions,
        "fields": ["had_moment", "duration", "intensity", "description"],
    },
    'sleep': {
        'model': SleepingLog,
        'fields': ['went_to_sleep_yesterday', 'wake_up_time', 'woke_up_during_night'],
        'questions': [
            {
                'field': 'went_to_sleep_yesterday',
                'question': "🕙 When did you go to sleep?",
                'type': 'time'
            },
            {
                'field': 'wake_up_time',
                'question': "⏰ When did you wake up?",
                'type': 'time'
            },
            {
                'field': 'woke_up_during_night',
                'question': "🌙 Did you wake up during the night?",
                'type': 'select',
                'options': ['yes', 'no']
            }
        ]
    },
    'food': {
    'model': FoodLog,
    'fields': [
        'breakfast_ate', 'breakfast_time',
        'lunch_ate', 'lunch_time',
        'dinner_ate', 'dinner_time'
    ],
    'questions': [
        {
            'field': 'breakfast_ate',
            'question': "🍳 Did you eat breakfast today?",
            'type': 'select',
            'options': ['yes', 'no']
        },
        {
            'field': 'breakfast_time',
            'question': "⏰ What time did you have breakfast?",
            'type': 'time',
            'condition': {
                'field': 'breakfast_ate',
                'value': 'yes'
            }
        },
        {
            'field': 'lunch_ate',
            'question': "🥗 Did you eat lunch today?",
            'type': 'select',
            'options': ['yes', 'no']
        },
        {
            'field': 'lunch_time',
            'question': "⏰ What time did you have lunch?",
            'type': 'time',
            'condition': {
                'field': 'lunch_ate',
                'value': 'yes'
            }
        },
        {
            'field': 'dinner_ate',
            'question': "🍽️ Did you eat dinner today?",
            'type': 'select',
            'options': ['yes', 'no']
        },
        {
            'field': 'dinner_time',
            'question': "⏰ What time did you have dinner?",
            'type': 'time',
            'condition': {
                'field': 'dinner_ate',
                'value': 'yes'
            }
        }
    ]
    },'sport': {
        'model': SportLog,
        'fields': ['did_sport', 'sport_type', 'other_sport', 'sport_time'],
        'questions': [
            {
                'field': 'did_sport',
                'question': "🏃‍♂️ Did you do any sport today?",
                'type': 'select',
                'options': ['yes', 'no']
            },
            {
                'field': 'sport_type',
                'question': "⚽ What type of sport did you do?",
                'type': 'select',
                'options': ['swimming', 'running', 'walking', 'gym', 'other'],
                'condition': {
                    'field': 'did_sport',
                    'value': 'yes'
                }
            },
            {
                'field': 'other_sport',
                'question': "📝 If other, please specify:",
                'type': 'text',
                'condition': {
                    'field': 'sport_type',
                    'value': 'other'
                }
            },
            {
                'field': 'sport_time',
                'question': "⏰ What time did you exercise?",
                'type': 'time',
                'condition': {
                    'field': 'did_sport',
                    'value': 'yes'
                }
            }
        ]
    },
    'meetings': {
    'model': Meetings,
    'fields': ['met_people', 'time', 'meeting_type', 'positivity_rating'],
    'questions': [
        {
            'field': 'met_people',
            'question': "👥 Did you meet anyone today?",
            'type': 'select',
            'options': ['yes', 'no']
        },
        {
            'field': 'time',
            'question': "⏰ What time did you meet them?",
            'type': 'time',
            'condition': {
                'field': 'met_people',
                'value': 'yes'
            }
        },
        {
            'field': 'meeting_type',
            'question': "📌 What kind of meeting was it?",
            'type': 'select',
            'options': ['family', 'friends', 'business', 'strangers'],
            'condition': {
                'field': 'met_people',
                'value': 'yes'
            }
        },
        {
            'field': 'positivity_rating',
            'question': "😊 How positive did the meeting feel? (1 = bad, 5 = great)",
            'type': 'select',
            'options': ['1', '2', '3', '4', '5'],
            'condition': {
                'field': 'met_people',
                'value': 'yes'
            }
        }
    ]
},
    'medication': {
        'model': None,
        'fields': [],
        'questions': get_medication_questions,
    },

}

@login_required
def category_summary(request, category):
    config = CATEGORY_CONFIG.get(category)
    if not config:
        return HttpResponseNotFound("Invalid category.")

    model = config['model']
    today =  localtime(tz_now()).date()


    try:
        instance = model.objects.get(user=request.user, date=today)
    except model.DoesNotExist:
        return redirect('dashboard:category_chat', category=category)

    fields = []
    for field in model._meta.fields:
        if field.name not in ('id', 'user', 'date'):
            value = getattr(instance, field.name)
            fields.append((field.verbose_name.title(), value))

    return render(request, 'dashboard/category_summary.html', {
        'category': category,
        'fields': fields,
    })

@login_required
def category_edit(request, category):
    today = tz_localtime().date()

    if category == "medication":
        medications = Medication.objects.filter(user=request.user)
        logs = MedicationLog.objects.filter(user=request.user, date=today)

        med_logs = {}

        for med in medications:
            raw_times = med.dose_times

            # 🔍 Fix: if it's a list with a single string like ['08:00,14:00'], flatten it
            if isinstance(raw_times, list) and len(raw_times) == 1 and isinstance(raw_times[0], str):
                times = [t.strip() for t in raw_times[0].split(",")]
            elif isinstance(raw_times, list):
                times = [t.strip() for t in raw_times]
            elif isinstance(raw_times, str):
                times = [t.strip() for t in raw_times.split(",")]
            else:
                times = []  # fallback
            doses = []
            for idx, t in enumerate(times):
                try:
                    if len(t.strip()) <= 4:
                        t = "0" + t  # e.g. 8:00 → 08:00
                    scheduled_time = datetime.strptime(t, "%H:%M").time()
                except ValueError:
                    scheduled_time = None

                existing_log = logs.filter(medication=med, dose_index=idx).first()
                doses.append({
                    "dose_index": idx,
                    "scheduled_time": scheduled_time,
                    "time_taken": existing_log.time_taken if existing_log else None
                })

            med_logs[med.id] = {
                "name": med.name,
                "doses": doses
            }

        import pprint
        pprint.pprint(med_logs)

        return render(request, 'dashboard/medication_edit.html', {
            'category': category,
            'med_logs': med_logs,
        })

    # fallback for other categories
    config = CATEGORY_CONFIG.get(category)
    if not config:
        return HttpResponseNotFound("Invalid category.")

    model = config['model']
    form_class = modelform_factory(model, exclude=["user", "date"])
    instance = model.objects.get(user=request.user, date=tz_localtime().date())
    form = form_class(instance=instance)

    return render(request, 'dashboard/category_edit.html', {
        'form': form,
        'category': category,
    })

@login_required
def category_update(request, category):
    today = tz_localtime().date()
    user = request.user

    if category == "medication":
        for key, value in request.POST.items():
            if key.startswith("time_") and value:
                try:
                    _, med_id, dose_index = key.split("_")
                    med = Medication.objects.get(id=med_id, user=request.user)
                    MedicationLog.objects.update_or_create(
                        user=request.user,
                        medication=med,
                        date=localtime(tz_now()).date(),
                        dose_index=int(dose_index),
                        defaults={"time_taken": datetime.strptime(value, "%H:%M").time()}
                    )
                except (ValueError, Medication.DoesNotExist):
                    continue
        return redirect('dashboard:dashboard_home')
    config = CATEGORY_CONFIG.get(category)
    if not config:
        return HttpResponseNotFound("Invalid category.")

    model = config['model']
    form_class = modelform_factory(model, exclude=["user", "date"])
    instance = model.objects.get(user=request.user, date= localtime(tz_now()).date())

    if request.method == "POST":
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('dashboard:dashboard_home')

    return render(request, 'dashboard/category_edit.html', {
        'form': form,
        'category': category,
    })

@login_required
def category_chat_page(request, category):
    config = CATEGORY_CONFIG.get(category)
    if not config and category != 'medication':
        return render(request, "dashboard/invalid_category.html")

    today =  localtime(tz_now()).date()

    if category == "medication":
        has_logs = MedicationLog.objects.filter(user=request.user, date=today).exists()
        
        if has_logs and not request.GET.get("edit"):
            logs = MedicationLog.objects.filter(user=request.user, date=today).select_related('medication')
            med_dict = {}
            for log in logs:
                key = log.medication.name
                med_dict.setdefault(key, []).append(log)
            return render(request, "dashboard/medication_summary.html", {
                "category": "medication",
                "med_logs": med_dict,
            })
        
        questions_func = config["questions"]
        questions = questions_func(request.user) if callable(questions_func) else []
        return render(request, "dashboard/chat.html", {
            "category": category,
            "questions": questions,
            "existing_data": {}
        })

    Model = config['model']
    existing_log = Model.objects.filter(user=request.user, date=today).first()

    if existing_log:
        return render(request, "dashboard/category_exists.html", {"category": category})

    questions = config["questions"](request.user) if callable(config["questions"]) else config["questions"]

    # Use the evaluated questions here!
    return render(request, "dashboard/chat.html", {
        "category": category,
        "questions": questions,  # <-- fix here
        "existing_data": {},
    })

@login_required
def category_chat_force(request, category):
    if category == "medication":
        questions = get_medication_questions(request.user)
        return render(request, "dashboard/chat.html", {
            "category": category,
            "questions": questions,
            "existing_data": {},
        })

    config = CATEGORY_CONFIG.get(category)
    if not config:
        return HttpResponseNotFound("Invalid category.")

    model = config["model"]
    questions = config["questions"](request.user) if callable(config["questions"]) else config["questions"]
    today =  localtime(tz_now()).date()

    try:
        instance = model.objects.get(user=request.user, date=today)
        return redirect('dashboard:category_summary', category=category)
    except model.DoesNotExist:
        return render(request, "dashboard/chat.html", {
            "category": category,
            "questions": questions,
            "existing_data": {},
        })

@csrf_exempt
@login_required
def category_chat_submit(request, category):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=400)

    data = json.loads(request.body)
    today = localtime(tz_now()).date()
    user = request.user

    # ✅ Handle Medication category specially
    if category == "medication":
        if data.get("meds_already_logged") == "📝 Update my log":
            # Handle update mode: update logs for all time fields provided
            for key, value in data.items():
                if key.startswith("time_") and value:
                    try:
                        _, med_id, dose_idx = key.split("_")
                        med = Medication.objects.get(id=med_id, user=user)

                        MedicationLog.objects.update_or_create(
                            user=user,
                            medication=med,
                            date=today,
                            dose_index=int(dose_idx),
                            defaults={"time_taken": datetime.strptime(value, "%H:%M").time()}
                        )
                    except (ValueError, Medication.DoesNotExist):
                        continue
            return JsonResponse({"status": "success"})


        # ✅ Handle regular time-block flow (morning, lunch, evening)
        for key, value in data.items():
            if key.startswith("took_") and value.lower() == "yes":
                try:
                    # Expected: took_<med_id>_<dose_index>
                    _, med_id, dose_index = key.split("_")
                    med = Medication.objects.get(id=med_id, user=user)

                    time_str = data.get(f"time_{med_id}_{dose_index}")
                    if not time_str:
                        continue

                    MedicationLog.objects.update_or_create(
                        user=user,
                        medication=med,
                        date=today,
                        dose_index=int(dose_index),
                        defaults={"time_taken": datetime.strptime(time_str, "%H:%M").time()}
                    )
                except (ValueError, Medication.DoesNotExist):
                    continue

        return JsonResponse({"status": "success"})

    # ✅ Handle other categories with standard logic
    config = CATEGORY_CONFIG.get(category)
    if not config:
        return JsonResponse({"error": "Invalid category"}, status=400)

    Model = config['model']
    fields = config['fields']
    field_data = {}

    for field in fields:
        if field in data:
            value = data[field]
            model_field = Model._meta.get_field(field)
            if isinstance(model_field, BooleanField):
                field_data[field] = value.lower() == 'yes'
            else:
                field_data[field] = value

    # Special logic for sport category
    if category == 'sport':
        did_sport = field_data.get('did_sport', False)
        sport_type = field_data.get('sport_type')
        other_sport = field_data.get('other_sport')

        if did_sport:
            if not sport_type:
                return JsonResponse({"error": "Please select a sport type."}, status=400)
            if sport_type == 'other' and (not other_sport or other_sport.strip() == ''):
                return JsonResponse({"error": "Please specify the other sport."}, status=400)
        else:
            field_data['sport_type'] = None
            field_data['other_sport'] = None
            field_data['sport_time'] = None

    Model.objects.update_or_create(
        user=request.user,
        date=today,
        defaults=field_data
    )

    return JsonResponse({"status": "success"})

def log_category(request, category):
    return render(request, 'dashboard/log_category.html', {'category': category})

@login_required
def dashboard_home(request):
    return render(request, "dashboard/dashboard.html")

def keep_alive(request):
    return JsonResponse({"status": "success"})

class DailyDocumentationView(LoginRequiredMixin, View):
    def get(self, request, date=None):
        today = datetime.date.today()
        date = date or today.strftime("%Y-%m-%d")

        documentation_data = {}
        if date != today.strftime("%Y-%m-%d"):
            documentation_data = fetch_documentation_for_date(date)

        context = {
            "date": date,
            "editable": date == today.strftime("%Y-%m-%d"),
            "documentation_data": documentation_data,
        }

        return render(request, "dashboard/dashboard.html", context)

@login_required
def log_medication(request, date):
    success_message = None
    error_message = None

    if request.method == "POST":
        time_taken_str = request.POST.get("time_taken")
        medication_id = request.POST.get("medication")

        if not time_taken_str or not medication_id:
            error_message = "Time and Medication selection are required."
        else:
            try:
                log_medication_entry(request.user, medication_id, date, time_taken_str)
                success_message = "Medication entry saved successfully!"
            except Exception as e:
                error_message = f"An error occurred: {e}"

    logs_for_date = MedicationLog.objects.filter(user=request.user, date=date)

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "date": date,
            "logs": logs_for_date,
            "success_message": success_message,
            "error_message": error_message,
        },
    )