from fastapi import APIRouter

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def status_check():
    return {"status": "Service is up and running!"}
