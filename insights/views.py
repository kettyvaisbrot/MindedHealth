from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from insights.services.log_fetcher import fetch_user_logs

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import os
import requests


# Use localhost when running both services locally.
# In Docker/K8s you’ll set INSIGHTS_SERVICE_URL to the service DNS (e.g. http://insights-service:8002)
INSIGHTS_SERVICE_URL = os.getenv("INSIGHTS_SERVICE_URL", "http://localhost:8002")


def serialize_logs(logs):
    serialized = {}
    for key, queryset in logs.items():
        serialized[key] = [
            {field.name: getattr(obj, field.name) for field in obj._meta.fields}
            for obj in queryset
        ]
    return serialized


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
        try:
            resp = requests.post(
                f"{INSIGHTS_SERVICE_URL}/api/v1/insights",
                json={"user_id": user.id, "logs": serialized_logs},
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
