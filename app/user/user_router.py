from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.user.user_schema import UserCreateRequest, UserLoginRequest, UserCreateResponse
from app.user.user_service import register_user, login_user
from app.user.user_auth import create_access_token

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register")
def register(body: UserCreateRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, body)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )
        data = UserCreateResponse(user) 
        return {
            "status": "success",
            "message": "User registered successfully",
            "data":data.model_dump()
        }
    except HTTPException as e:
        raise 
    except Exception as e:
        logger.error(f"Error registering user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user"
        )

@router.post("/login")
def login(body: UserLoginRequest, db: Session = Depends(get_db)):
    try:
        user = login_user(db, body.username, body.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        access_token = create_access_token(data={"sub": user.user_id})
        
        return {
            "status": "success",
            "message": "Login successful",
            "data":{ 
                "access_token": access_token, 
                "token_type": "bearer"
            }
        }
    except Exception as e:
        logger.error(f"Error logging in user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging in user"
        )