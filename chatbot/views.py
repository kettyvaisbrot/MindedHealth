# chatbot/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .ai_chatbot import (
    generate_ai_response,
)  # Import the function that interacts with OpenAI
from django.shortcuts import render


@csrf_exempt  # This decorator is necessary for allowing POST requests without CSRF protection for now
def chatbot_response(request):
    if request.method == "POST":
        try:
            # Parse the incoming request data
            data = json.loads(request.body)  # Get the JSON payload
            user_input = data.get(
                "user_input", ""
            )  # Extract the user input from the payload

            if not user_input:
                return JsonResponse({"error": "User input is required"}, status=400)

            # Get the response from OpenAI
            ai_response = generate_ai_response(user_input)

            # Return the AI's response in JSON format
            return JsonResponse({"response": ai_response}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


def chatbot_page(request):
    return render(request, "chatbot/chat.html")
