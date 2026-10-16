"""api/routers/health.py — Health check endpoint."""

from fastapi import APIRouter

from api.schemas.common import HealthResponse
from core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, include_in_schema=True)
async def health() -> HealthResponse:
    """
    Basic liveness probe. Returns 200 when the application is running.
    Does not check DB connectivity (use a readiness probe for that in Phase 7).
    """
    return HealthResponse(
        status="ok",
        version="0.1.0",
        environment=settings.app_env,
    )
