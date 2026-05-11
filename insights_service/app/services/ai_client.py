import os
import requests

AI_SERVICE_URL = os.getenv(
    "AI_SERVICE_URL",
    "http://localhost:8001"
)

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


def get_ai_insight(prompt: str) -> str:
    response = requests.post(
        f"{AI_SERVICE_URL}/generate-insight",
        json={"prompt": prompt},
        headers={"X-Internal-Key": INTERNAL_API_KEY},
        timeout=15,
    )

    response.raise_for_status()
    return response.json()["insight"]
