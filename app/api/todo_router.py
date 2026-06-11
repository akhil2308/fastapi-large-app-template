from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import User, get_current_user
from app.core.database import get_db
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.core.settings import settings
from app.schemas.todo_schema import Todo, TodoCreate, TodoUpdate
from app.services.todo_service import (
    create_todo_service,
    delete_todo_service,
    get_todos_service,
    update_todo_service,
)
from app.utils.rate_limiter import RateLimit

router = APIRouter()
SERVICE = "todo"


@router.post(
    "/",
    summary="Create a new To-Do",
    status_code=status.HTTP_201_CREATED,
    tags=["Todo"],
    response_model=ApiResponse[Todo],
    dependencies=[
        Depends(
            RateLimit(SERVICE, scope="user", per_min=settings.rate_limit.write_per_min)
        )
    ],
    responses={
        429: {"description": "Write limit exceeded"},
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
    data = await create_todo_service(current_user.user_id, body, db)
    return {
        "status": "success",
        "message": "Todo created successfully",
        "data": data,
    }


@router.get(
    "/",
    summary="List all To-Dos",
    status_code=status.HTTP_200_OK,
    tags=["Todo"],
    response_model=PaginatedApiResponse[Todo],
    dependencies=[
        Depends(
            RateLimit(SERVICE, scope="user", per_min=settings.rate_limit.read_per_min)
        )
    ],
    responses={
        429: {"description": "Read limit exceeded"},
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


@router.put(
    "/{todo_id}",
    summary="Update a To-Do",
    status_code=status.HTTP_200_OK,
    tags=["Todo"],
    response_model=ApiResponse[Todo],
    dependencies=[
        Depends(
            RateLimit(SERVICE, scope="user", per_min=settings.rate_limit.write_per_min)
        )
    ],
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
    updated_todo = await update_todo_service(todo_id, current_user.user_id, body, db)
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


@router.delete(
    "/{todo_id}",
    summary="Delete a To-Do",
    status_code=status.HTTP_200_OK,
    tags=["Todo"],
    response_model=ApiResponse[None],
    dependencies=[
        Depends(
            RateLimit(SERVICE, scope="user", per_min=settings.rate_limit.write_per_min)
        )
    ],
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
    deleted = await delete_todo_service(todo_id, current_user.user_id, db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    return {
        "status": "success",
        "message": "Todo deleted successfully",
    }
