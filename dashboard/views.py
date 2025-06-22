from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
import datetime
import json
import requests
from .models import FoodLog, SportLog, SleepingLog, Meetings, SeizureLog
from .serializers import (
    FoodLogSerializer,
    SportLogSerializer,
    SleepingLogSerializer,
    MeetingsSerializer,
    SeizureLogSerializer,
)
from django.contrib import messages
from datetime import datetime
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
from .services.medication_service import (
    get_user_medications_and_logs,
    save_medication_log,
)
from .services.food_service import (
    get_food_logs,
    get_food_log_or_404,
    create_or_update_food_log,
    update_food_log,
    delete_food_log,
)
from .services.sport_service import (
    get_sport_logs,
    get_sport_log_or_404,
    create_or_update_sport_log,
    update_sport_log,
    delete_sport_log,
)
from .services.sleeping_service import (
    get_sleeping_logs,
    get_sleeping_log_or_404,
    create_or_update_sleeping_log,
    delete_sleeping_log,
)
from .services.meetings_service import (
    get_meetings_by_date,
    get_meeting_or_404,
    create_or_update_meeting,
    update_meeting,
    delete_meeting,
)
from .services.seizure_service import (
    get_seizure_logs,
    get_seizure_log_or_404,
    create_or_update_seizure_log,
    delete_seizure_log,
)

@login_required
def dashboard_home(request):
    date_str = request.GET.get("date", "")
    today = timezone.now().date()
    context = {"today": today.strftime("%Y-%m-%d")}

    if not date_str:
        messages.warning(request, "Date is required before displaying data.")
        return render(request, "dashboard/dashboard.html", context)

    date = parse_date_from_str(date_str)
    if not date:
        messages.warning(request, "Invalid date format. Please use YYYY-MM-DD.")
        return render(request, "dashboard/dashboard.html", context)

    logs = fetch_dashboard_logs(request.user, date)

    context.update({
        "date": date,
        "is_current_date": date == today,
        **logs,
        "sport_choices": SportLog.SPORT_CHOICES,
        "meeting_type_choices": Meetings.MEETING_TYPES_CHOICES,
    })

    return render(request, "dashboard/dashboard.html", context)


class MedicationLogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date = request.GET.get("date", timezone.now().date().strftime("%Y-%m-%d"))
        medications, medication_logs = get_user_medications_and_logs(request.user, date)

        context = {
            "medications": medications,
            "medication_logs": medication_logs,
            "today": timezone.now().date(),
            "selected_date": date,
        }
        return render(request, "dashboard/log_medication.html", context)

    def post(self, request):
        date = request.data.get("date", timezone.now().date().strftime("%Y-%m-%d"))
        data = request.data.copy()
        data["user"] = request.user.id
        serializer = MedicationLogSerializer(data=data)

        if serializer.is_valid():
            save_medication_log(request.user, date, serializer.validated_data)
            return HttpResponseRedirect(reverse("dashboard:dashboard_home") + f"?date={date}")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def keep_alive(request):
    return JsonResponse({"status": "success"})


class FoodLogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve food logs for a specific date.",
        responses={200: FoodLogSerializer(many=True), 404: "No food log for this date"},
    )
    def get(self, request, date):
        food_logs = get_food_logs(request.user, date)
        if food_logs.exists():
            serializer = FoodLogSerializer(food_logs, many=True)
            return Response(serializer.data)
        return Response(
            {"message": "No food log for this date"},
            status=status.HTTP_404_NOT_FOUND,
        )

    @swagger_auto_schema(
        operation_description="Create or update a food log for a specific date.",
        request_body=FoodLogSerializer,
        responses={302: "Redirects to dashboard after successful save", 400: "Validation errors"},
    )
    def post(self, request):
        serializer = FoodLogSerializer(data=request.data)
        if serializer.is_valid():
            create_or_update_food_log(request.user, serializer.validated_data)
            date = serializer.validated_data.get("date")
            return HttpResponseRedirect(reverse("dashboard:dashboard_home") + f"?date={date}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Update an existing food log for a specific date.",
        request_body=FoodLogSerializer,
        responses={200: FoodLogSerializer, 404: "Food log not found for this date", 400: "Validation errors"},
    )
    def put(self, request, date):
        food_log = get_food_log_or_404(request.user, date)
        serializer = FoodLogSerializer(food_log, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a food log for a specific date.",
        responses={200: "Food log deleted successfully", 404: "Food log not found for this date"},
    )
    def delete(self, request, date):
        food_log = get_food_log_or_404(request.user, date)
        delete_food_log(food_log)
        return Response({"message": "Food log deleted successfully"})

class SportLogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        sport_logs = get_sport_logs(request.user, date)
        if sport_logs.exists():
            serializer = SportLogSerializer(sport_logs, many=True)
            return Response(serializer.data)
        return Response(
            {"message": "No Sport log for this date"},
            status=status.HTTP_404_NOT_FOUND,
        )

    def post(self, request):
        serializer = SportLogSerializer(data=request.data)
        if serializer.is_valid():
            create_or_update_sport_log(request.user, serializer.validated_data)
            date = serializer.validated_data.get("date")
            return HttpResponseRedirect(reverse("dashboard:dashboard_home") + f"?date={date}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, date):
        sport_log = get_sport_log_or_404(request.user, date)
        serializer = SportLogSerializer(sport_log, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, date):
        sport_log = get_sport_log_or_404(request.user, date)
        delete_sport_log(sport_log)
        return Response({"message": "Sport log deleted successfully"})


class SleepingLogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        sleeping_logs = get_sleeping_logs(request.user, date)
        if sleeping_logs.exists():
            serializer = SleepingLogSerializer(sleeping_logs, many=True)
            return Response(serializer.data)
        return Response(
            {"message": "No sleeping log for this date"},
            status=status.HTTP_404_NOT_FOUND,
        )

    def post(self, request):
        serializer = SleepingLogSerializer(data=request.data)
        if serializer.is_valid():
            create_or_update_sleeping_log(request.user, serializer.validated_data)
            date = serializer.validated_data.get("date")
            return HttpResponseRedirect(reverse("dashboard:dashboard_home") + f"?date={date}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, date):
        sleeping_log = get_sleeping_log_or_404(request.user, date)
        serializer = SleepingLogSerializer(sleeping_log, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, date):
        sleeping_log = get_sleeping_log_or_404(request.user, date)
        delete_sleeping_log(sleeping_log)
        return Response({"message": "Sleeping log deleted successfully"})
    

class MeetingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        meetings_logs = get_meetings_by_date(request.user, date)
        if meetings_logs.exists():
            serializer = MeetingsSerializer(meetings_logs, many=True)
            return Response(serializer.data)
        return Response(
            {"message": "No meetings log for this date"},
            status=status.HTTP_404_NOT_FOUND,
        )

    def post(self, request):
        serializer = MeetingsSerializer(data=request.data)
        if serializer.is_valid():
            create_or_update_meeting(request.user, serializer.validated_data)
            date = serializer.validated_data.get("date")
            return HttpResponseRedirect(reverse("dashboard:dashboard_home") + f"?date={date}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        meeting = get_meeting_or_404(pk)
        serializer = MeetingsSerializer(meeting, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Meeting updated successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        meeting = get_meeting_or_404(pk)
        delete_meeting(meeting)
        return Response({"message": "Meeting deleted successfully"})

class SeizureLogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        seizure_logs = get_seizure_logs(request.user, date)
        if seizure_logs.exists():
            serializer = SeizureLogSerializer(seizure_logs, many=True)
            return Response(serializer.data)
        return Response(
            {"message": "No seizure logs for this date"},
            status=status.HTTP_404_NOT_FOUND,
        )

    def post(self, request):
        serializer = SeizureLogSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            create_or_update_seizure_log(request.user, serializer.validated_data)
            date = serializer.validated_data.get("date")
            return HttpResponseRedirect(reverse("dashboard:dashboard_home") + f"?date={date}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        seizure_log = get_seizure_log_or_404(pk)
        serializer = SeizureLogSerializer(seizure_log, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        seizure_log = get_seizure_log_or_404(pk)
        delete_seizure_log(seizure_log)
        return Response(status=status.HTTP_204_NO_CONTENT)


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