import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", tags=["Health"], summary="Service Health Check")
async def status_check():
    """
    Health check endpoint to verify that the service is running.
    """
    return {"status": "Service is up and running!"}
