import os
import requests

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-microservice:8001")

def get_ai_insight(prompt: str) -> str:
    try:
        response = requests.post(
            f"{AI_SERVICE_URL}/generate-insight",
            json={"prompt": prompt},
            timeout=15
        )
        response.raise_for_status()
        return response.json().get("insight", "")
    except Exception as e:
        return f"AI service unavailable: {str(e)}"