from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from app.database import Base

class User(Base):
    
    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id         = Column(String, unique=True, index=True, nullable=False)
    username        = Column(String, unique=True, nullable=False)
    email           = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __tablename__ = 'users'