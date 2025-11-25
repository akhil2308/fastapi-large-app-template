from datetime import datetime

from pydantic import BaseModel


class TodoCreate(BaseModel):
    title: str
    description: str | None = None


class TodoUpdate(BaseModel):
    title: str
    description: str | None = None
    completed: bool = False


class Todo(BaseModel):
    id: int
    todo_id: str
    user_id: str
    title: str
    description: str | None = None
    completed: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
