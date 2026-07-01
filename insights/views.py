from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from insights.services.log_fetcher import fetch_user_logs
from users.internal_tokens import generate_internal_service_token

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import os
import requests


# Use localhost when running both services locally.
# In Docker/K8s you’ll set INSIGHTS_SERVICE_URL to the service DNS (e.g. http://insights-service:8002)
INSIGHTS_SERVICE_URL = os.getenv("INSIGHTS_SERVICE_URL", "http://localhost:8002")


def _time_str(t):
    return t.strftime("%H:%M:%S") if t else None


def _compute_sleep_hours(obj):
    from datetime import datetime, timedelta
    if obj.went_to_sleep_yesterday and obj.wake_up_time:
        sleep_dt = datetime.combine(datetime.today(), obj.went_to_sleep_yesterday)
        wake_dt = datetime.combine(datetime.today(), obj.wake_up_time)
        if wake_dt <= sleep_dt:
            wake_dt += timedelta(days=1)
        return round((wake_dt - sleep_dt).total_seconds() / 3600, 2)
    return None


def serialize_logs(logs):
    return {
        "food": [
            {
                "date": str(obj.date),
                "breakfast_ate": obj.breakfast_ate,
                "lunch_ate": obj.lunch_ate,
                "dinner_ate": obj.dinner_ate,
            }
            for obj in logs.get("food", [])
        ],
        "sport": [
            {
                "date": str(obj.date),
                "did_sport": obj.did_sport,
                "sport_type": obj.sport_type,
                "other_sport": obj.other_sport,
            }
            for obj in logs.get("sport", [])
        ],
        "sleep": [
            {
                "date": str(obj.date),
                "went_to_sleep_yesterday": _time_str(obj.went_to_sleep_yesterday),
                "wake_up_time": _time_str(obj.wake_up_time),
                "woke_up_during_night": obj.woke_up_during_night,
                "hours": _compute_sleep_hours(obj),
            }
            for obj in logs.get("sleep", [])
        ],
        "meetings": [
            {
                "date": str(obj.date),
                "time": _time_str(obj.time),
                "meeting_type": obj.meeting_type,
                "positivity_rating": obj.positivity_rating,
            }
            for obj in logs.get("meetings", [])
        ],
        "medications": [
            {
                "date": str(obj.date),
                "taken": obj.time_taken is not None,
            }
            for obj in logs.get("medications", [])
        ],
        "felt_off": [
            {
                "date": str(obj.date),
                "had_moment": obj.had_moment,
                "duration": obj.duration,
                "intensity": obj.intensity,
                "description": obj.description,
            }
            for obj in logs.get("felt_off", [])
        ],
    }


class AIInsightsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve AI-generated mental health insights based on user's recent activity logs",
        responses={
            200: openapi.Response(
                "Successful Response",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "insights": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="The AI-generated insight text",
                        ),
                    },
                ),
            )
        },
    )
    def get(self, request):
        user = request.user

        # 1) Fetch logs from Django DB
        logs = fetch_user_logs(user)

        # 2) Serialize QuerySets to JSON-friendly payload
        serialized_logs = serialize_logs(logs)

        # 3) Call insights_service (it handles Redis caching + metrics + prompt + AI)
        # Issue a short-lived internal service JWT scoped to insights-service.
        # This replaces the former X-Internal-Key shared secret.
        internal_token = generate_internal_service_token(
            user_id=user.id,
            user_role=user.role,
            audience="insights-service",
        )

        try:
            resp = requests.post(
                f"{INSIGHTS_SERVICE_URL}/api/v1/insights",
                json={"user_id": user.id, "logs": serialized_logs},
                headers={"Authorization": f"Bearer {internal_token}"},
                timeout=30,
            )
            resp.raise_for_status()
            return Response(resp.json())

        except requests.RequestException as e:
            # Temporary fallback (don’t crash the UI)
            return Response(
                {"insights": "⚠️ Insights service is temporarily unavailable. Please try again later."},
                status=503,
            )


@login_required
def insights_page_view(request):
    return render(request, "insights/insights.html")
