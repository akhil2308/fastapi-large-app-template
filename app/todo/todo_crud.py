import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.todo.todo_model import Todo


def create_todo(db: Session, user_id: str, title: str, description: str):
    new_todo = Todo(
        todo_id=str(uuid.uuid4()),
        user_id=user_id,
        title=title,
        description=description,
        completed=False
    )
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo

def get_todos_by_offset(db: Session, user_id: str, offset: int = 0, limit: int = 100):
    return db.query(Todo).filter(Todo.user_id == user_id).offset(offset).limit(limit).all()

# different implementation of get_todos_by_offset
def get_todos_by_page_number(db: Session, user_id: str, page_number: int = 0, page_size: int = 100):
    offset = (page_number - 1) * page_size
    return db.query(Todo).filter(Todo.user_id == user_id).offset(offset).limit(page_size).all()

def get_todos_total_size(db: Session, user_id: str):
    return db.query(Todo).filter(Todo.user_id == user_id).count()

def get_todos_by_todo_id(db: Session, todo_id: str, user_id: str):
    return db.query(Todo).filter(Todo.todo_id == todo_id, Todo.user_id == user_id).first()

def update_todo_by_todo_id(db: Session, todo_id: str, user_id: str, title: str, description: str, completed: bool):
    todo_obj = get_todos_by_todo_id(db, todo_id, user_id)
    if not todo_obj:
        return None
    if title is not None:
        todo_obj.title = title
    if description is not None:
        todo_obj.description = description
    if completed is not None:
        todo_obj.completed = completed
    db.commit()
    db.refresh(todo_obj)
    return todo_obj

def delete_todo_by_todo_id(db: Session, todo_id: str, user_id: str):
    todo_obj = get_todos_by_todo_id(db, todo_id, user_id)
    if not todo_obj:
        return None
    todo_obj.is_deleted = True
    todo_obj.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(todo_obj)