# chatbot/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .ai_chatbot import (
    generate_ai_response,
)
from django.shortcuts import render
from chatbot.services.chatbot_service import get_ai_chat_response
from django.contrib.auth.decorators import login_required

@csrf_exempt
def chatbot_response(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        user_input = data.get("user_input", "")

        response = get_ai_chat_response(user_input)
        return JsonResponse({"response": response}, status=200)

    except ValueError as ve:
        return JsonResponse({"error": str(ve)}, status=400)

    except Exception as e:
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)


@login_required
def chatbot_page(request):
    return render(request, "chatbot/chat.html")
