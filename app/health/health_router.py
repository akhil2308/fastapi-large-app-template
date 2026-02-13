import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", tags=["Health"], summary="Service Health Check")
async def status_check(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint to verify that the service is running.
    Checks connectivity to Redis and PostgreSQL.
    """
    health_status = {"status": "healthy", "service": "up and running"}

    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "disconnected"
        health_status["status"] = "unhealthy"

    # Check Redis connectivity
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

    return health_status
