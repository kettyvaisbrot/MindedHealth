
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
        logs = fetch_user_logs(request.user)

        if not any(log.exists() for log in logs.values()):
            message = "😊 It’s time to get to know each other! Start documenting your day-to-day life via the dashboard."
            return Response({"insights": message})

        prompt = build_insight_prompt(logs)
        ai_response = get_ai_insight(prompt)

        return Response({"insights": ai_response})

@login_required
def insights_page_view(request):
    return render(request, "insights/insights.html")
