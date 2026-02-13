import time
from contextlib import asynccontextmanager

from app.observability.metrics import record_db_query


@asynccontextmanager
async def db_timed(name: str, operation: str = "query"):
    """
    Async context manager to time database queries.

    Usage:
        async with db_timed("create_todo", operation="insert"):
            todo = await todo_crud.create(db_session, body)

    Args:
        name: Name/identifier for the query (e.g., "create_todo", "get_user")
        operation: Type of database operation (select, insert, update, delete)
    """
    start = time.time_ns()
    try:
        yield
    finally:
        duration_ms = (time.time_ns() - start) / 1e6
        record_db_query(name, duration_ms, operation)
