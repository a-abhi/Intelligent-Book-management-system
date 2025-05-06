from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models import User, Log
from db import get_db
from auth import verify_credentials, security
from pydantic import BaseModel, EmailStr
from fastapi.security import HTTPBasicCredentials
from logging_utils import log_request, log_error
import traceback

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class LogCreate(BaseModel):
    user_id: int
    service: str
    action: str
    status: str

router = APIRouter()

@router.post("/auth/register")
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        user = User(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Log successful registration
        log_request(
            endpoint="/auth/register",
            method="POST",
            status_code=200,
            user_id=str(user.id)
        )
        
        # Create log entry for registration
        log = Log(
            user_id=user.id,
            service="auth",
            action="register",
            status="success"
        )
        db.add(log)
        await db.commit()
        
        return {"user_id": user.id}
        
    except IntegrityError as e:
        await db.rollback()
        error_msg = "Username or email already exists"
        log_error("/auth/register", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        await db.rollback()
        log_error("/auth/register", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/auth/login")
async def login(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await verify_credentials(credentials, db)
        
        # Log successful login
        log_request(
            endpoint="/auth/login",
            method="POST",
            status_code=200,
            user_id=str(user.id)
        )
        
        # Create log entry for login
        log = Log(
            user_id=user.id,
            service="auth",
            action="login",
            status="success"
        )
        db.add(log)
        await db.commit()
        
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }
    except HTTPException as e:
        log_request(
            endpoint="/auth/login",
            method="POST",
            status_code=e.status_code,
            error=str(e.detail)
        )
        raise e
    except Exception as e:
        log_error("/auth/login", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logs")
async def log_action(
    request: Request,
    log_data: LogCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        log = Log(
            user_id=log_data.user_id,
            service=log_data.service,
            action=log_data.action,
            status=log_data.status
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        
        log_request(
            endpoint="/logs",
            method="POST",
            status_code=200,
            user_id=str(log_data.user_id)
        )
        
        return {"log_id": log.id}
        
    except Exception as e:
        await db.rollback()
        log_error("/logs", e, str(log_data.user_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create log entry"
        )

@router.get("/health")
async def health_check(request: Request):
    try:
        log_request(
            endpoint="/health",
            method="GET",
            status_code=200
        )
        return {"ping": "pong"}
    except Exception as e:
        log_error("/health", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        ) 