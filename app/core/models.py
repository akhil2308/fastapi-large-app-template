"""
Central registry for all SQLAlchemy models.
Imported by Alembic to populate Base.metadata.
"""

from app.core.database import Base
from app.todo.todo_model import Todo
from app.user.user_model import User

__all__ = ["Base", "User", "Todo"]
