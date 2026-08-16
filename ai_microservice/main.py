import os
import logging
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import jwt

from internal_jwt import validate_internal_jwt

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)

client = OpenAI()

app = FastAPI()

failure_count = 0
FAILURE_THRESHOLD = 5


class PromptInput(BaseModel):
    prompt: str


@app.get("/health")
def health():
    # Deliberately does not call OpenAI -- an upstream OpenAI outage is
    # already handled by the circuit breaker below and shouldn't make Docker
    # restart an otherwise-healthy container.
    return {"status": "ok"}


def verify_internal_jwt_header(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization[len("Bearer "):]
    try:
        validate_internal_jwt(token)
    except jwt.exceptions.PyJWTError as exc:
        logger.warning("Invalid internal JWT: %s", exc)
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/generate-insight")
def generate_insight(data: PromptInput, authorization: Optional[str] = Header(None)):
    verify_internal_jwt_header(authorization)

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
