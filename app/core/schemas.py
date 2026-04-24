from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status: str
    message: str
    data: T | None = None


class PaginatedApiResponse(BaseModel, Generic[T]):
    status: str
    message: str
    data: list[T]
    total_size: int
    page_number: int
    page_size: int
    total_pages: int
