from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserCreateResponse(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    created_at: datetime
    
    class Config:
        from_attributes = True
    
class UserLoginRequest(BaseModel):
    username: str
    password: str
