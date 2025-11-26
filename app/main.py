from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from logging.config import dictConfig

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis

from app.core.logging_config import log_config
from app.core.settings import CoreConfig, RedisConfig
from app.health.health_router import router as health_router
from app.todo.todo_router import router as todo_router
from app.user.user_router import router as user_router

dictConfig(log_config)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # startup
    # Create Redis connection pool
    redis = Redis(
        host=RedisConfig.HOST,
        port=RedisConfig.PORT,
        db=RedisConfig.DB,
        password=RedisConfig.PASSWORD,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=RedisConfig.CONNECTION_TIMEOUT,
        socket_keepalive=True,  # Enable TCP keepalive
        retry_on_timeout=True,  # Retry on timeout errors
        max_connections=RedisConfig.MAX_CONNECTIONS,
        health_check_interval=RedisConfig.HEALTH_CHECK_INTERVAL,
    )

    try:
        # verify connection
        try:
            await redis.ping()
        except ConnectionError as e:
            raise RuntimeError("Redis connection failed") from e

        # init limiter using the redis client
        await FastAPILimiter.init(redis)

        # store redis on app.state for later use
        app.state.redis = redis

        yield  # application runs after this point

    finally:
        # shutdown
        await app.state.redis.close()
        await FastAPILimiter.close()


app = FastAPI(
    title="FastAPI Large APP Template",
    description="A production-ready template for building scalable FastAPI applications with modular architecture and essential integrations.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Network/Server Level	(For Allowing Server to Server Communication)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=CoreConfig.ALLOWED_HOSTS)

# Protection from Browser/Application Level (For Allowing Browser to Server Communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CoreConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers=["*"],  # ["Content-Type", "Authorization"]
)

app.include_router(health_router, prefix="/api/v1/health", tags=["Health"])
app.include_router(user_router, prefix="/api/v1/user", tags=["User"])
app.include_router(todo_router, prefix="/api/v1/todo", tags=["Todo"])


# Exception Handlers for uniform error response
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation Failed",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "errors": getattr(exc, "errors", None),
        },
    )
