from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


def _utc_now() -> datetime:
    """Return current UTC datetime with timezone info."""
    return datetime.now(UTC)


class Todo(Base):
    id = Column(Integer, primary_key=True, index=True)
    todo_id = Column(String, nullable=False, unique=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)

    __tablename__ = "todos"
