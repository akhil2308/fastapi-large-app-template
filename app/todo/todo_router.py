from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session

from app.utils.auth_dependency import get_current_user, User
from app.utils.rate_limiter import user_rate_limiter
from app.settings import READ_RATE_LIMITING_PER_MIN, WRITE_RATE_LIMITING_PER_MIN
from app.database import get_db
from app.todo.todo_schema import Todo, TodoCreate
from app.todo.todo_service import create_todo_service, get_todos_serivce

import logging
logger = logging.getLogger(__name__)

router = APIRouter()
SERVICE = "todo"

@router.post("/")
async def create_todo(
    body: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):
    try:
        await user_rate_limiter(current_user.user_id, SERVICE, READ_RATE_LIMITING_PER_MIN)
        data = await create_todo_service(current_user.user_id, body, db)
        return {
            "status": "success",
            "message": "Todo created successfully",
            "data": data
        }
    except HTTPException as e:
        raise  
    except Exception as e:  
        logger.error(f"Error creating todo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating todo"
        )

@router.get("/")
async def get_todos(
    page_number: int = Query(1, ge=1),
    page_size: int = Query(10, gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):
    try:
        await user_rate_limiter(current_user.user_id, SERVICE, WRITE_RATE_LIMITING_PER_MIN)
        data = await get_todos_serivce(current_user.user_id, page_number, page_size, db)
        return {
            "status": "success",
            "message": "Todos retrieved successfully",
            "data": data['data'],
            "total_size": data['total_size']
        }
    except HTTPException as e:
        raise  
    except Exception as e:
        logger.error(f"Error getting todos: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting todos"
        )