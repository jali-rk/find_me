"""
Health check endpoint.
"""

from fastapi import APIRouter

from app.domain.models import HealthResponse

router = APIRouter()


# Copilot: Create FastAPI health check endpoint returning {"status": "ok"}
@router.get("/healthz", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    Returns 200 OK if service is running.
    """
    return HealthResponse(status="ok")
