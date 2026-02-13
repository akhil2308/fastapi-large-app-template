from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None


class Todo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    todo_id: str
    user_id: str
    title: str
    description: str | None = None
    completed: bool = False
    created_at: datetime
    updated_at: datetime
