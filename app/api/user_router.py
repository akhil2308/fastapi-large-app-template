import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import User, get_current_user, oauth2_scheme
from app.core.auth import create_access_token, create_refresh_token
from app.core.database import get_db
from app.core.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.core.schemas import ApiResponse
from app.core.settings import RateLimitConfig
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
from app.utils.rate_limiter import ip_rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter()
AUTH_SERVICE = "auth"


@router.post(
    "/register",
    summary="Register a new user",
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
    response_model=ApiResponse[UserCreateResponse],
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
        await ip_rate_limiter(
            request, f"{AUTH_SERVICE}:register", RateLimitConfig.WRITE_PER_MIN
        )
        user = await register_user(db, body)
        return {
            "status": "success",
            "message": "User registered successfully",
            "data": user,
        }
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
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
    response_model=ApiResponse[LoginResponseData],
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
    Authenticates a user and returns a JWT access token and refresh token.
    """
    try:
        await ip_rate_limiter(
            request, f"{AUTH_SERVICE}:login", RateLimitConfig.WRITE_PER_MIN
        )
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
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging in user",
        ) from e


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
):
    """
    Invalidates the current access token by adding it to the blacklist.
    """
    try:
        await logout_user(token)
        return {"status": "success", "message": "Logged out successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging out user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging out",
        ) from e


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
):
    """
    Issues a new access token and refresh token. The old refresh token is rotated (invalidated).
    """
    try:
        tokens = await refresh_tokens(db, body.refresh_token)
        return {
            "status": "success",
            "message": "Token refreshed successfully",
            "data": tokens,
        }
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token",
        ) from e
