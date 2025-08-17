from dashboard.category_config import CATEGORY_CONFIG
from django.utils.timezone import localtime, now as tz_now
from drf_yasg.utils import swagger_auto_schema
import datetime
from django.db.models import BooleanField
from django.forms import modelform_factory
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from medications.models import MedicationLog, Medication
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .services.documentation_service import fetch_documentation_for_date
from .services.medication_service import log_medication_entry
from .services.questions_service import get_medication_questions
from drf_yasg import openapi
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import localtime, now
from django.http import HttpResponseNotFound, JsonResponse
from django.utils.decorators import method_decorator
from datetime import datetime


def get_bool_query_param(request, param_name):
    val = request.GET.get(param_name)
    return str(val).lower() in ("true", "1", "yes")


class CategorySummaryView(APIView):
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Get a summary of today's data for a given category (e.g., sleep, food, exercise). "
                              "Returns the documented fields if data exists, otherwise redirects to chat page.",
        manual_parameters=[
            openapi.Parameter(
                'category',
                openapi.IN_PATH,
                description="Name of the category (e.g., 'sleep', 'food', 'sports', etc.)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(description="Summary data for the category"),
            302: openapi.Response(description="No data found, redirect to chat page"),
            404: openapi.Response(description="Invalid category"),
        }
    )
    def get(self, request, category):
        config = CATEGORY_CONFIG.get(category)
        if not config:
            return Response({"error": "Invalid category."}, status=404)

        today = localtime(tz_now()).date()
        model = config.get("model")

        if category == "medication" or model is None:
            # Special case for medication logs
            logs = MedicationLog.objects.filter(user=request.user, date=today).select_related("medication")
            if not logs.exists():
                return Response({"redirect": f"/dashboard/{category}/chat"}, status=302)

            med_logs = {}
            for log in logs:
                med_name = log.medication.name
                med_logs.setdefault(med_name, []).append({
                    "dose_index": log.dose_index,
                    "time_taken": log.time_taken.isoformat() if log.time_taken else None,
                })

            return Response({
                "category": category,
                "med_logs": med_logs,
            })

        # Generic categories:
        instance = model.objects.filter(user=request.user, date=today).first()
        if not instance:
            return Response({"redirect": f"/dashboard/{category}/chat"}, status=302)

        fields = []
        for field in model._meta.fields:
            if field.name not in ("id", "user", "date"):
                value = getattr(instance, field.name)
                fields.append({"label": field.verbose_name.title(), "value": value})

        return Response({
            "category": category,
            "fields": fields,
        })


@login_required
def category_summary_page(request, category):
    if category == "medication":
        template_name = 'dashboard/medication_summary.html'
    else:
        template_name = 'dashboard/category_summary.html'

    return render(request, template_name, {'category': category})


@method_decorator(login_required, name='dispatch')
class CategoryEditView(APIView):
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Retrieve editable log data for a specific category (e.g., sleep, mood) for today.",
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_PATH, description="Log category", type=openapi.TYPE_STRING),
        ],
        responses={200: 'Success', 404: 'Not Found'}
    )
    def get(self, request, category):
        today = localtime(now()).date()

        if category == "medication":
            medications = Medication.objects.filter(user=request.user)
            logs = MedicationLog.objects.filter(user=request.user, date=today)

            med_logs = {}

            for med in medications:
                raw_times = med.dose_times
                if isinstance(raw_times, list) and len(raw_times) == 1 and isinstance(raw_times[0], str):
                    times = [t.strip() for t in raw_times[0].split(",")]
                elif isinstance(raw_times, list):
                    times = [t.strip() for t in raw_times]
                elif isinstance(raw_times, str):
                    times = [t.strip() for t in raw_times.split(",")]
                else:
                    times = []

                doses = []
                for idx, t in enumerate(times):
                    try:
                        if len(t.strip()) <= 4:
                            t = "0" + t
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

            return render(request, 'dashboard/medication_edit.html', {
                'category': category,
                'med_logs': med_logs,
            })

        config = CATEGORY_CONFIG.get(category)
        if not config:
            return HttpResponseNotFound("Invalid category.")

        model = config['model']
        instance = get_object_or_404(model, user=request.user, date=today)
        form_class = modelform_factory(model, exclude=["user", "date"])
        form = form_class(instance=instance)

        return render(request, 'dashboard/category_edit.html', {
            'form': form,
            'category': category,
        })

    def post(self, request, category):
        today = localtime(now()).date()

        if category == "medication":
            for key, value in request.POST.items():
                if key.startswith("time_") and value:
                    try:
                        _, med_id, dose_index = key.split("_")
                        med = Medication.objects.get(id=med_id, user=request.user)
                        MedicationLog.objects.update_or_create(
                            user=request.user,
                            medication=med,
                            date=today,
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
        instance = get_object_or_404(model, user=request.user, date=today)
        form_class = modelform_factory(model, exclude=["user", "date"])
        form = form_class(request.POST, instance=instance)

        if form.is_valid():
            form.save()
            return redirect('dashboard:dashboard_home')

        return render(request, 'dashboard/category_edit.html', {
            'form': form,
            'category': category,
        })


class CategoryChatView(APIView):
    permission_classes = []

    @swagger_auto_schema(
        operation_description="""
        Fetch questions or existing data for a given category to support chat-based data entry.

        - If a log already exists and `force=false`, a summary or message is returned instead of questions.
        - If `force=true`, forces showing the questions again even if data exists.
        - If `edit=true` for medication, shows editable form again even if logs exist.

        Used to power the conversational documentation experience in the dashboard.
        """,
        manual_parameters=[
            openapi.Parameter(
                'category',
                openapi.IN_PATH,
                description="The category to fetch questions for (e.g., 'sleep', 'food', 'medication').",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'force',
                openapi.IN_QUERY,
                description="Force showing questions even if data exists (true/false).",
                type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'edit',
                openapi.IN_QUERY,
                description="Edit mode for medication logs (true/false).",
                type=openapi.TYPE_BOOLEAN
            ),
        ],
        responses={
            200: openapi.Response(description="Questions or existing data returned."),
            404: openapi.Response(description="Invalid category."),
        }
    )
    def get(self, request, category):
        today = localtime(tz_now()).date()
        force = get_bool_query_param(request, "force")
        edit = get_bool_query_param(request, "edit")

        if category == "medication":
            logs = MedicationLog.objects.filter(user=request.user, date=today).select_related("medication")
            has_logs = logs.exists()

            if has_logs and not edit and not force:
                med_dict = {}
                for log in logs:
                    key = log.medication.name
                    med_dict.setdefault(key, []).append({
                        "time_taken": log.time_taken,
                        "dose_index": log.dose_index,
                    })
                return Response({
                    "category": "medication",
                    "summary": med_dict,
                })

            # When edit=true OR force=true — return questions + existing data
            questions = get_medication_questions(request.user)
            existing_data = {}
            for log in logs:
                med_name = log.medication.name
                existing_data.setdefault(med_name, []).append({
                    "dose_index": log.dose_index,
                    "time_taken": log.time_taken.isoformat() if log.time_taken else None,
                })

            return Response({
                "category": "medication",
                "questions": questions,
                "existing_data": existing_data,
            })

        # Handle all other categories (generic case)
        config = CATEGORY_CONFIG.get(category)
        if not config:
            return Response({"error": "Invalid category."}, status=404)

        model = config.get("model")
        if not model:
            return Response({"error": "Model not defined for this category."}, status=500)

        existing_log = model.objects.filter(user=request.user, date=today).first()
        if existing_log and not force:
            return Response({"message": "Log already exists", "category": category})

        questions = config["questions"](request.user) if callable(config["questions"]) else config["questions"]

        return Response({
            "category": category,
            "questions": questions,
            "existing_data": {},
        })


@login_required
def chat_page(request, category):
    user = request.user
    today = localtime(tz_now()).date()
    force = get_bool_query_param(request, "force")

    config = CATEGORY_CONFIG.get(category)
    if not config:
        return render(request, "dashboard/404.html", status=404)

    if category == "medication":
        existing_log = MedicationLog.objects.filter(user=user, date=today).first()
    else:
        Model = config.get("model")
        if Model is None:
            existing_log = None
        else:
            existing_log = Model.objects.filter(user=user, date=today).first()

    if existing_log and not force:
        return render(request, "dashboard/category_exists.html", {"category": category})

    return render(request, "dashboard/chat.html", {"category": category})


class CategoryChatSubmitView(APIView):
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Get summary data for a category",
        manual_parameters=[
            openapi.Parameter(
                'category',
                openapi.IN_PATH,
                description="Category name",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'force',
                openapi.IN_QUERY,
                description="Force refetch",
                type=openapi.TYPE_BOOLEAN
            )
        ],
        responses={
            200: openapi.Response(description="Success"),
            404: openapi.Response(description="Not found")
        }
    )
    def get(self, request, category):
        user = request.user
        today = localtime(tz_now()).date()

        existing_log = self._get_today_log(user, category, today)
        if existing_log:
            # Render your 'log exists' HTML page if data exists for today
            return render(request, "dashboard/log_exists.html", {
                "category": category,
            })

        # Otherwise render the chat start page for this category
        return render(request, f"dashboard/chat_{category}.html", {
            "category": category,
            "start_chat": True,
        })

    @swagger_auto_schema(
        operation_description="""
        Submit chat data for a specific category.

        - For **medication**:
            - If `meds_already_logged = "📝 Update my log"`: updates existing logs based on `time_<med_id>_<dose_index>` keys.
            - If submitting time-block answers: each `took_<med_id>_<dose_index> = yes` is logged along with `time_<med_id>_<dose_index>`.

        - For **generic categories** (e.g., mood, food, sleep):
            - Submits category-specific fields (e.g., `ate_today`, `slept_well`) and updates the log for today.

        - For **sport**:
            - If `did_sport` is false or not provided, all other sport-related fields are nulled out.

        Returns a success message upon valid submission.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            additional_properties=openapi.Schema(type=openapi.TYPE_STRING),
            example={
                "meds_already_logged": "📝 Update my log",
                "time_5_0": "08:00",
                "time_5_1": "20:00",
                "took_5_0": "yes",
                "time_5_0": "08:00",
                "did_sport": "yes",
                "sport_time": "30",
                "sport_type": "Running"
            }
        ),
        responses={
            200: openapi.Response(
                description="Log submitted successfully",
                examples={
                    "application/json": {"status": "success"}
                }
            ),
            400: openapi.Response(
                description="Invalid category",
                examples={
                    "application/json": {"error": "Invalid category"}
                }
            )
        }
    )
    def post(self, request, category):
        data = request.data
        today = localtime(tz_now()).date()
        user = request.user

        if category == "medication":
            if data.get("meds_already_logged") == "📝 Update my log":
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
                return Response({"status": "success"})

            # time-block flow
            for key, value in data.items():
                if key.startswith("took_") and value.lower() == "yes":
                    try:
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
            return Response({"status": "success"})

        # Generic categories
        config = CATEGORY_CONFIG.get(category)
        if not config:
            return Response({"error": "Invalid category"}, status=400)

        Model = config["model"]
        fields = config["fields"]
        field_data = {}

        for field in fields:
            if field in data:
                model_field = Model._meta.get_field(field)
                val = data[field]
                if isinstance(model_field, BooleanField):
                    field_data[field] = val.lower() == "yes"
                else:
                    field_data[field] = val

        # Sport logic
        if category == "sport":
            if not field_data.get("did_sport"):
                field_data["sport_type"] = None
                field_data["other_sport"] = None
                field_data["sport_time"] = None

        Model.objects.update_or_create(user=user, date=today, defaults=field_data)
        return Response({"status": "success"})


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
