from pydantic import BaseModel


class LivenessResponse(BaseModel):
    status: str


class DetailedHealthResponse(BaseModel):
    status: str
    service: str
    database: str | None = None
    redis: str | None = None
