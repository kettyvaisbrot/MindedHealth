import os
import requests

AI_SERVICE_URL = os.getenv(
    "AI_SERVICE_URL",
    "http://localhost:8001"
)


def get_ai_insight(prompt: str, internal_token: str) -> str:
    # internal_token is the same internal-service JWT this service received
    # from Django (aud includes 'ai-service') — forwarded as-is, since this
    # service never holds the private key needed to mint its own token.
    response = requests.post(
        f"{AI_SERVICE_URL}/generate-insight",
        json={"prompt": prompt},
        headers={"Authorization": f"Bearer {internal_token}"},
        timeout=15,
    )

    response.raise_for_status()
    return response.json()["insight"]
