from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.utils import utc_now


class Todo(Base):
    __tablename__ = "todos"
    __table_args__ = (
        Index(
            "ix_todos_user_active_created",
            "user_id",
            "is_deleted",
            text("created_at DESC"),
            text("id DESC"),
            postgresql_where=text("is_deleted = false"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    todo_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
