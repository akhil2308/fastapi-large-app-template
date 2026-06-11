from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import User, get_current_user, get_redis, oauth2_scheme
from app.core.auth import create_access_token, create_refresh_token
from app.core.database import get_db
from app.core.schemas import ApiResponse
from app.core.settings import settings
from app.schemas.user_schema import (
    LoginResponseData,
    RefreshRequest,
    TokenPair,
    UserCreateRequest,
    UserCreateResponse,
    UserLoginRequest,
)
from app.services.user_service import (
    login_user,
    logout_user,
    refresh_tokens,
    register_user,
)
from app.utils.rate_limiter import RateLimit

router = APIRouter()


@router.post(
    "/register",
    summary="Register a new user",
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
    response_model=ApiResponse[UserCreateResponse],
    dependencies=[
        Depends(
            RateLimit(
                "auth:register", scope="ip", per_min=settings.rate_limit.write_per_min
            )
        )
    ],
    responses={
        400: {"description": "Username or email already exists"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal Server Error"},
    },
)
async def register(
    body: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new user account.
    Returns the user data upon successful registration.
    """
    user = await register_user(db, body)
    return {
        "status": "success",
        "message": "User registered successfully",
        "data": user,
    }


@router.post(
    "/login",
    summary="Login to get access token",
    status_code=status.HTTP_200_OK,
    tags=["Authentication"],
    response_model=ApiResponse[LoginResponseData],
    dependencies=[
        Depends(
            RateLimit(
                "auth:login", scope="ip", per_min=settings.rate_limit.write_per_min
            )
        )
    ],
    responses={
        401: {"description": "Invalid credentials (wrong username or password)"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal Server Error"},
    },
)
async def login(
    body: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticates a user and returns a JWT access token and refresh token.
    """
    user = await login_user(db, body.username, body.password)
    access_token = create_access_token(data={"sub": user.user_id})
    refresh_token = create_refresh_token(data={"sub": user.user_id})
    return {
        "status": "success",
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    }


@router.post(
    "/logout",
    summary="Logout and invalidate access token",
    status_code=status.HTTP_200_OK,
    tags=["Authentication"],
    response_model=ApiResponse[None],
    responses={
        401: {"description": "Invalid or expired token"},
        500: {"description": "Internal Server Error"},
    },
)
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    """
    Invalidates the current access token by adding it to the blacklist.
    """
    await logout_user(redis, token)
    return {"status": "success", "message": "Logged out successfully"}


@router.post(
    "/refresh",
    summary="Refresh access token",
    status_code=status.HTTP_200_OK,
    tags=["Authentication"],
    response_model=ApiResponse[TokenPair],
    responses={
        401: {"description": "Invalid or expired refresh token"},
        500: {"description": "Internal Server Error"},
    },
)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Issues a new access token and refresh token. The old refresh token is rotated (invalidated).
    """
    tokens = await refresh_tokens(db, redis, body.refresh_token)
    return {
        "status": "success",
        "message": "Token refreshed successfully",
        "data": tokens,
    }
