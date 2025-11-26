import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.settings import RateLimitConfig
from app.todo.todo_schema import TodoCreate
from app.todo.todo_service import create_todo_service, get_todos_serivce
from app.utils.auth_dependency import User, get_current_user
from app.utils.rate_limiter import user_rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter()
SERVICE = "todo"


@router.post(
    "/",
    summary="Create a new To-Do",
    status_code=status.HTTP_201_CREATED,
    tags=["Todo"],
    responses={
        429: {"description": "Daily write limit exceeded"},
        500: {"description": "Internal Server Error"},
    },
)
async def create_todo(
    body: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new Todo item.
    Requires 'todo_write' permissions.
    """
    try:
        assert current_user.user_id is not None
        await user_rate_limiter(
            current_user.user_id, SERVICE, RateLimitConfig.READ_PER_MIN
        )
        data = await create_todo_service(current_user.user_id, body, db)
        return {
            "status": "success",
            "message": "Todo created successfully",
            "data": data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating todo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating todo",
        ) from e


@router.get(
    "/",
    summary="List all To-Dos",
    status_code=status.HTTP_200_OK,
    tags=["Todo"],
    responses={
        429: {"description": "Daily read limit exceeded"},
        500: {"description": "Internal Server Error"},
    },
)
async def get_todos(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, gt=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a paginated list of Todo items for the current user.
    """
    try:
        assert current_user.user_id is not None
        await user_rate_limiter(
            current_user.user_id, SERVICE, RateLimitConfig.WRITE_PER_MIN
        )
        data = await get_todos_serivce(current_user.user_id, page_number, page_size, db)
        return {
            "status": "success",
            "message": "Todos retrieved successfully",
            "data": data["data"],
            "total_size": data["total_size"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting todos: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting todos",
        ) from e
