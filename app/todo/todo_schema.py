from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class TodoUpdate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class Todo(BaseModel):
    id: int
    todo_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True