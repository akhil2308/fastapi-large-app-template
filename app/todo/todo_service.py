from sqlalchemy.orm import Session
from typing import List
from app.todo.todo_crud import create_todo, get_todos_by_page_number, get_todos_total_size
from app.todo.todo_schema import TodoCreate, Todo


def create_todo_service(user_id: str, todo_data: TodoCreate, db: Session):
    new_todo = create_todo(db, user_id, todo_data.title, todo_data.description)
    return Todo.model_validate(new_todo)


def get_todos_serivce(user_id: str, page_number: int, page_size: int, db: Session):
    user_todos = get_todos_by_page_number(db, user_id, page_number, page_size)
    total_count = get_todos_total_size(db, user_id)
    return {
        "data": [Todo.model_validate(todo) for todo in user_todos],
        "total_size": total_count
    }