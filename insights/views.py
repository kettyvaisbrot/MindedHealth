from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from insights.services.log_fetcher import fetch_user_logs
from insights.services.prompt_builder import build_insight_prompt
from insights.services.ai_client import get_ai_insight
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from insights.services.metrics_computer import compute_metrics, compute_correlations
from django.http import JsonResponse
import traceback
import redis
import json
import hashlib
from datetime import date
import os
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=6379,
    db=0
)

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
        responses={200: openapi.Response('Successful Response', schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'insights': openapi.Schema(type=openapi.TYPE_STRING, description='The AI-generated insight text'),
            },
        ))},
    )

    def get(self, request):
        user = request.user
        today_str = str(date.today())
        cache_key = f"insights:{user.id}:{today_str}"

        print("\n==============================", flush=True)
        print(">>> AIInsightsAPIView CALLED", flush=True)
        print(">>> USER:", user.id, flush=True)
        print(">>> CACHE KEY:", cache_key, flush=True)

        # Fetch logs
        logs = fetch_user_logs(user)

        # If no logs → simple message
        if not any(log.exists() for log in logs.values()):
            print(">>> NO LOGS FOUND — returning default message", flush=True)
            return Response({
                "insights": "😊 It’s time to get to know each other! Start documenting your day-to-day life via the dashboard."
            })

        # Serialize logs for hashing
        serialized_logs = serialize_logs(logs)
        logs_json = json.dumps(serialized_logs, sort_keys=True, default=str)
        data_hash = hashlib.sha256(logs_json.encode()).hexdigest()

        print(">>> DATA HASH:", data_hash, flush=True)

        # Try to read from Redis
        cached = redis_client.get(cache_key)

        if cached:
            print(">>> REDIS VALUE FOUND", flush=True)
            cached = json.loads(cached.decode("utf-8"))

            print(">>> CACHED HASH:", cached.get("data_hash"), flush=True)

            if cached.get("data_hash") == data_hash:
                print(">>> CACHE HIT — returning cached insights", flush=True)
                print("==============================\n", flush=True)
                return Response({"insights": cached["insight"]})
            else:
                print(">>> CACHE MISMATCH — logs changed, regenerating", flush=True)
        else:
            print(">>> NO REDIS ENTRY FOUND — cache miss", flush=True)

        # Cache miss — regenerate insights
        print(">>> GENERATING NEW INSIGHTS...", flush=True)
        metrics = compute_metrics(logs)
        correlations = compute_correlations(logs, metrics)
        prompt = build_insight_prompt(logs, metrics=metrics, correlations=correlations)

        ai_response = get_ai_insight(prompt)

        # Save to Redis (24 hours)
        redis_client.set(
            cache_key,
            json.dumps({"insight": ai_response, "data_hash": data_hash}),
            ex=60 * 60 * 24
        )

        print(">>> NEW INSIGHTS SAVED TO REDIS", flush=True)
        print("==============================\n", flush=True)

        return Response({"insights": ai_response})




@login_required
def insights_page_view(request):
    return render(request, "insights/insights.html")
