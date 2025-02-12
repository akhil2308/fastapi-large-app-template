import uuid
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.user.user_model import User

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_username_or_email(db: Session, username: str = None, email: str = None):
    return db.query(User).filter(or_(User.username == username, User.email == email)).first()

def get_user_by_user_id(db: Session, user_id: str):
    return db.query(User).filter(User.user_id == user_id).first()

def create_user(db: Session, username: str, email: str, hashed_password: str):
    user = User(
        user_id=str(uuid.uuid4()),
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
