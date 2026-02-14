from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


def _utc_now() -> datetime:
    """Return current UTC datetime with timezone info."""
    return datetime.now(UTC)


class User(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    __tablename__ = "users"
