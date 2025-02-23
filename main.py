import uvicorn
from redis.asyncio import Redis
from fastapi_limiter import FastAPILimiter
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.health.health_router import router as health_router
from app.user.user_router import router as user_router
from app.todo.todo_router import router as todo_router
from app.database import engine
from app.settings import *

import logging
logging.config.dictConfig(logging_config)

# Create tables (only locally for production, create the tables in the database)
from app.user import user_model
from app.todo import todo_model

async def create_tables(engine):
    """Async table creation entrypoint"""
    async with engine.begin() as conn:
        await conn.run_sync(todo_model.Base.metadata.create_all)
        await conn.run_sync(user_model.Base.metadata.create_all)


app = FastAPI(
    title="FastAPI Large APP Template",
    description="A production-ready template for building scalable FastAPI applications with modular architecture and essential integrations.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url = "/openapi.json",
)

@app.on_event("startup")
async def startup():
    # Create tables in the database (only locally, Comment for production)
    await create_tables(engine)
    
    # Create Redis connection pool
    redis = await Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=REDIS_CONNECTION_TIMEOUT,
        socket_keepalive=True,        # Enable TCP keepalive
        retry_on_timeout=True,        # Retry on timeout errors
        max_connections=REDIS_MAX_CONNECTIONS,
        health_check_interval=REDIS_HEALTH_CHECK_INTERVAL
    )
    
    # Verify connection
    try:
        await redis.ping()
    except ConnectionError as e:
        raise RuntimeError("Redis connection failed") from e
    
    await FastAPILimiter.init(redis)
    # app.state.redis = redis  # Store for access in other parts

@app.on_event("shutdown")
async def shutdown():
    # await app.state.redis.close()
    await FastAPILimiter.close()


# Network/Server Level	(For Allowing Server to Server Communication)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)

# Protection from Browser/Application Level (For Allowing Browser to Server Communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"], # ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers=["*"], # ["Content-Type", "Authorization"]
)

app.include_router(health_router, prefix="/v1/api/health", tags=["Health"])
app.include_router(user_router, prefix="/v1/api/user", tags=["User"])
app.include_router(todo_router, prefix="/v1/api/todo", tags=["Todo"])


# Exception Handlers for uniform error response
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation Failed",
            "errors": exc.errors()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "errors": getattr(exc, "errors", None)
        }
    )


if __name__ == '__main__':
    uvicorn.run("main:app", host='0.0.0.0', port=8000, log_level="info", reload=True, log_config=logging_config)