from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base
from app.core.utils import utc_now


class Todo(Base):
    id = Column(Integer, primary_key=True, index=True)
    todo_id = Column(String, nullable=False, unique=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False)

    __tablename__ = "todos"
