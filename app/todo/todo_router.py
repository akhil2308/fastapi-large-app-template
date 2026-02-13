import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.settings import RateLimitConfig
from app.todo.todo_crud import delete_todo_by_todo_id, update_todo_by_todo_id
from app.todo.todo_schema import TodoCreate, TodoUpdate
from app.todo.todo_service import create_todo_service, get_todos_service
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
            current_user.user_id, SERVICE, RateLimitConfig.WRITE_PER_MIN
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
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a paginated list of Todo items for the current user.
    """
    try:
        assert current_user.user_id is not None
        await user_rate_limiter(
            current_user.user_id, SERVICE, RateLimitConfig.READ_PER_MIN
        )
        data = await get_todos_service(current_user.user_id, page_number, page_size, db)
        return {
            "status": "success",
            "message": "Todos retrieved successfully",
            "data": data["data"],
            "total_size": data["total_size"],
            "page_number": data["page_number"],
            "page_size": data["page_size"],
            "total_pages": data["total_pages"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting todos: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting todos",
        ) from e


@router.put(
    "/{todo_id}",
    summary="Update a To-Do",
    status_code=status.HTTP_200_OK,
    tags=["Todo"],
    responses={
        404: {"description": "Todo not found"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal Server Error"},
    },
)
async def update_todo(
    body: TodoUpdate,
    todo_id: str = Path(..., description="The ID of the todo to update"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing Todo item.
    """
    try:
        assert current_user.user_id is not None
        await user_rate_limiter(
            current_user.user_id, SERVICE, RateLimitConfig.WRITE_PER_MIN
        )
        updated_todo = await update_todo_by_todo_id(
            db,
            todo_id,
            current_user.user_id,
            title=body.title,
            description=body.description,
            completed=body.completed,
        )
        if not updated_todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found",
            )
        return {
            "status": "success",
            "message": "Todo updated successfully",
            "data": updated_todo,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating todo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating todo",
        ) from e


@router.delete(
    "/{todo_id}",
    summary="Delete a To-Do",
    status_code=status.HTTP_200_OK,
    tags=["Todo"],
    responses={
        404: {"description": "Todo not found"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal Server Error"},
    },
)
async def delete_todo(
    todo_id: str = Path(..., description="The ID of the todo to delete"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a Todo item (soft delete).
    """
    try:
        assert current_user.user_id is not None
        await user_rate_limiter(
            current_user.user_id, SERVICE, RateLimitConfig.WRITE_PER_MIN
        )
        deleted = await delete_todo_by_todo_id(db, todo_id, current_user.user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found",
            )
        return {
            "status": "success",
            "message": "Todo deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting todo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting todo",
        ) from e
