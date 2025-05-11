from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str


class LogCreate(BaseModel):
    user_id: int
    service: str
    action: str
    status: str


class LogResponse(BaseModel):
    log_id: int
    timestamp: datetime
