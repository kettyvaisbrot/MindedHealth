import os
import logging
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)

client = OpenAI()

app = FastAPI()

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

failure_count = 0
FAILURE_THRESHOLD = 5


class PromptInput(BaseModel):
    prompt: str


def verify_internal_key(x_internal_key: Optional[str] = Header(None)):
    if not x_internal_key or x_internal_key != INTERNAL_API_KEY:
        logger.warning("Unauthorized request to ai_microservice: invalid or missing X-Internal-Key")
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/generate-insight")
def generate_insight(data: PromptInput, x_internal_key: Optional[str] = Header(None)):
    verify_internal_key(x_internal_key)

    global failure_count

    if failure_count >= FAILURE_THRESHOLD:
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable. Please try again later."
        )

    try:
        messages = [
            {"role": "system", "content": "You are a compassionate mental health assistant."},
            {"role": "user", "content": data.prompt},
        ]

        response = call_openai_with_retry(messages)
        content = response.choices[0].message.content

        failure_count = 0
        return {"insight": content.strip()}

    except Exception:
        failure_count += 1
        raise HTTPException(
            status_code=500,
            detail="Failed to generate insight"
        )


def call_openai_with_retry(messages, retries=3, timeout_seconds=10):
    last_exception = None

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=700,
                temperature=0.7,
                timeout=timeout_seconds,
            )
            return response

        except Exception as e:
            last_exception = e
            time.sleep(2 ** attempt)

    raise last_exception
