from fastapi import FastAPI
from app.api.insights import router as insights_router

app = FastAPI(title="Insights Service")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(insights_router)
