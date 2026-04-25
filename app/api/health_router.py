import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class LivenessResponse(BaseModel):
    status: str


class DetailedHealthResponse(BaseModel):
    status: str
    service: str
    database: str | None = None
    redis: str | None = None


@router.get(
    "/",
    tags=["Health"],
    summary="Liveness Check",
    response_model=LivenessResponse,
)
async def liveness():
    """Lightweight liveness probe — confirms the process is running."""
    return {"status": "ok"}


@router.get(
    "/detailed",
    tags=["Health"],
    summary="Detailed Health Check",
    response_model=DetailedHealthResponse,
    responses={503: {"description": "One or more services are unavailable"}},
)
async def detailed_health_check(request: Request, db: AsyncSession = Depends(get_db)):
    """Readiness probe — checks connectivity to PostgreSQL and Redis."""
    health_status = {"status": "healthy", "service": "up and running"}

    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "disconnected"
        health_status["status"] = "unhealthy"

    try:
        redis = request.app.state.redis if hasattr(request.app.state, "redis") else None
        if redis:
            await redis.ping()
            health_status["redis"] = "connected"
        else:
            health_status["redis"] = "not configured"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["redis"] = "disconnected"
        health_status["status"] = "unhealthy"

    if health_status["status"] == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status,
        )
    return health_status
