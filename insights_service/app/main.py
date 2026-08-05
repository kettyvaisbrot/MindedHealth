from fastapi import FastAPI, Response
from app.api.insights import router as insights_router
from app.services.redis_client import redis_client

app = FastAPI(title="Insights Service")

@app.get("/health")
def health(response: Response):
    try:
        redis_client.ping()
    except Exception as exc:
        response.status_code = 503
        return {"status": "error", "component": "redis", "detail": str(exc)}
    return {"status": "ok"}

app.include_router(insights_router)
