from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from datetime import datetime
from app.database import Base

class Todo(Base):
    
    id          = Column(Integer, primary_key=True, index=True)
    todo_id     = Column(String, nullable=False, unique=True)
    user_id     = Column(String, nullable=False)
    title       = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    completed   = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at  = Column(DateTime, nullable=True)
    is_deleted  = Column(Boolean, default=False)
    
    __tablename__ = "todos"
