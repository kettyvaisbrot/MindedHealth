import json
import hashlib
from datetime import date
from app.services.metrics_computer import compute_metrics, compute_correlations
from app.services.redis_client import redis_client
from app.services.prompt_builder import build_insight_prompt
from app.services.ai_client import get_ai_insight


CACHE_TTL_SECONDS = 60 * 60 * 24  # 24 hours


def generate_insights(user_id: int, logs: dict) -> str:
    today_str = str(date.today())
    cache_key = f"insights:{user_id}:{today_str}"

    # If no logs at all
    if not any(logs.get(k) for k in logs.keys()):
        return (
            "😊 It’s time to get to know each other! "
            "Start documenting your day-to-day life via the dashboard."
        )

    # Hash logs
    logs_json = json.dumps(logs, sort_keys=True, default=str)
    data_hash = hashlib.sha256(logs_json.encode()).hexdigest()

    # Try Redis
    cached = redis_client.get(cache_key)

    if cached:
        cached = json.loads(cached)
        if cached.get("data_hash") == data_hash:
            return cached["insight"]

    # Cache miss → compute
    metrics = compute_metrics(logs)
    correlations = compute_correlations(logs, metrics)
    prompt = build_insight_prompt(
        logs,
        metrics=metrics,
        correlations=correlations,
    )

    insight_text = get_ai_insight(prompt)

    # Save to Redis
    redis_client.set(
        cache_key,
        json.dumps(
            {
                "insight": insight_text,
                "data_hash": data_hash,
            }
        ),
        ex=CACHE_TTL_SECONDS,
    )

    return insight_text
