from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)


class TodoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    completed: bool | None = None

    @model_validator(mode="after")
    def _require_at_least_one_field(self) -> "TodoUpdate":
        if self.title is None and self.description is None and self.completed is None:
            raise ValueError("At least one field must be provided to update a todo")
        return self


class Todo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    todo_id: str
    title: str
    description: str | None = None
    completed: bool = False
    created_at: datetime
    updated_at: datetime
