from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.settings import *

SQLALCHEMY_DATABASE_URL = f'postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_NAME}'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size = POSTGRES_POOL_SIZE, 
    max_overflow = POSTGRES_MAX_OVERFLOW, 
    pool_recycle = 300,
    pool_pre_ping=True, # for postgres only
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()