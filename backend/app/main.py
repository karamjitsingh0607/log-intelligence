
from fastapi import FastAPI

from app.api.logs import router as logs_router
from app.api.jobs import router as jobs_router

app = FastAPI(
    title="Distributed Log Intelligence",
    description="Scalable log ingestion and AI-assisted analysis.",
    version="0.1.0",
)

app.include_router(logs_router)
app.include_router(jobs_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "distributed-log-intelligence",
    }


@app.get("/")
def root():
    return {
        "message": "Welcome to Distributed Log Intelligence",
        "docs": "/docs",
    }
