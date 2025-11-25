import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.user.user_auth import create_access_token
from app.user.user_schema import UserCreateRequest, UserLoginRequest
from app.user.user_service import login_user, register_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register")
async def register(body: UserCreateRequest, db: AsyncSession = Depends(get_db)):
    try:
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


@router.post("/login")
async def login(body: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
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
