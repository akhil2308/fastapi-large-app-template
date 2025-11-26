import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.todo.todo_model import Todo


async def create_todo(
    db: AsyncSession, user_id: str, title: str, description: str | None = None
) -> Todo:
    new_todo = Todo(
        todo_id=str(uuid.uuid4()),
        user_id=user_id,
        title=title,
        description=description,
        completed=False,
    )
    db.add(new_todo)
    await db.commit()
    await db.refresh(new_todo)
    return new_todo


async def get_todos_by_offset(
    db: AsyncSession, user_id: str, offset: int = 0, limit: int = 100
) -> Sequence[Todo]:
    result = await db.execute(
        select(Todo).where(Todo.user_id == user_id).offset(offset).limit(limit)
    )
    return result.scalars().all()


async def get_todos_by_page_number(
    db: AsyncSession, user_id: str, page_number: int = 1, page_size: int = 100
) -> Sequence[Todo]:
    offset = (page_number - 1) * page_size
    result = await db.execute(
        select(Todo).where(Todo.user_id == user_id).offset(offset).limit(page_size)
    )
    return result.scalars().all()


async def get_todos_total_size(db: AsyncSession, user_id: str) -> int | None:
    result = await db.execute(
        select(func.count(Todo.todo_id)).where(Todo.user_id == user_id)
    )
    return result.scalar()


async def get_todos_by_todo_id(db: AsyncSession, todo_id: str, user_id: str):
    result = await db.execute(
        select(Todo).where(Todo.todo_id == todo_id, Todo.user_id == user_id)
    )
    return result.scalars().first()


async def update_todo_by_todo_id(
    db: AsyncSession,
    todo_id: str,
    user_id: str,
    title: str | None = None,
    description: str | None = None,
    completed: bool | None = None,
) -> Todo | None:
    # Get existing todo
    todo_obj = await get_todos_by_todo_id(db, todo_id, user_id)
    if not todo_obj:
        return None

    # Build update dictionary
    update_data: dict[str, Any] = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if completed is not None:
        update_data["completed"] = completed

    # Perform update
    await db.execute(
        update(Todo)
        .where(Todo.todo_id == todo_id, Todo.user_id == user_id)
        .values(**update_data)
    )
    await db.commit()
    await db.refresh(todo_obj)
    return todo_obj


async def delete_todo_by_todo_id(db: AsyncSession, todo_id: str, user_id: str) -> None:
    # Soft delete implementation
    await db.execute(
        update(Todo)
        .where(Todo.todo_id == todo_id, Todo.user_id == user_id)
        .values(is_deleted=True, deleted_at=datetime.utcnow())
    )
    await db.commit()
