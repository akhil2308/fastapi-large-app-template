from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base
from app.core.utils import utc_now


class User(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __tablename__ = "users"
