import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.settings import RateLimitConfig
from app.user.user_auth import create_access_token
from app.user.user_schema import UserCreateRequest, UserLoginRequest
from app.user.user_service import login_user, register_user
from app.utils.rate_limiter import ip_rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter()
AUTH_SERVICE = "auth"


@router.post(
    "/register",
    summary="Register a new user",
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
    responses={
        400: {"description": "Username or email already exists"},
        500: {"description": "Internal Server Error"},
    },
)
async def register(
    body: UserCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new user account.
    Returns the user data upon successful registration.
    """
    try:
        # Rate limit by IP to prevent abuse
        await ip_rate_limiter(
            request, f"{AUTH_SERVICE}:register", RateLimitConfig.WRITE_PER_MIN
        )
        user = await register_user(db, body)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists",
            )
        return {
            "status": "success",
            "message": "User registered successfully",
            "data": user,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user",
        ) from e


@router.post(
    "/login",
    summary="Login to get access token",
    status_code=status.HTTP_200_OK,
    tags=["Authentication"],
    responses={
        401: {"description": "Invalid credentials (wrong username or password)"},
        500: {"description": "Internal Server Error"},
    },
)
async def login(
    body: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticates a user and returns a JWT access token.
    """
    try:
        # Rate limit by IP to prevent brute force attacks
        await ip_rate_limiter(
            request, f"{AUTH_SERVICE}:login", RateLimitConfig.WRITE_PER_MIN
        )
        user = await login_user(db, body.username, body.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )
        access_token = create_access_token(data={"sub": user.user_id})

        return {
            "status": "success",
            "message": "Login successful",
            "data": {"access_token": access_token, "token_type": "bearer"},
        }
    except Exception as e:
        logger.error(f"Error logging in user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging in user",
        ) from e
