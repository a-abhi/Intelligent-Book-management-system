from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models import User, Log
from db import get_db
from utils.auth import verify_credentials, security
from fastapi.security import HTTPBasicCredentials
from utils.logging import log_request, log_error
from schemas import UserCreate, UserResponse, LogCreate, LogResponse
import traceback

class SharedServiceRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1", tags=["shared"])
        self._setup_routes()
    
    def _setup_routes(self):
        # Auth Routes
        @self.router.post("/auth/register", response_model=UserResponse)
        async def register(
            request: Request,
            user_data: UserCreate,
            db: AsyncSession = Depends(get_db)
        ):
            try:
                # Create user
                user = User(
                    username=user_data.username,
                    email=user_data.email,
                    password=user_data.password
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                
                # Log request
                log_request(
                    endpoint="/auth/register",
                    method="POST",
                    status_code=200,
                    user_id=str(user.id)
                )
                
                # Create log entry
                log = Log(
                    user_id=user.id,
                    service="auth",
                    action="register",
                    status="success"
                )
                db.add(log)
                await db.commit()
                
                return UserResponse(
                    user_id=user.id,
                    username=user.username,
                    email=user.email
                )
                
            except IntegrityError as e:
                await db.rollback()
                log_error("/auth/register", e)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already exists"
                )
            except Exception as e:
                await db.rollback()
                log_error("/auth/register", e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Registration failed"
                )
        
        @self.router.post("/auth/login", response_model=UserResponse)
        async def login(
            request: Request,
            credentials: HTTPBasicCredentials = Depends(security),
            db: AsyncSession = Depends(get_db)
        ):
            try:
                # Verify credentials
                user = await verify_credentials(credentials, db)
                
                # Log request
                log_request(
                    endpoint="/auth/login",
                    method="POST",
                    status_code=200,
                    user_id=str(user.id)
                )
                
                # Create log entry
                log = Log(
                    user_id=user.id,
                    service="auth",
                    action="login",
                    status="success"
                )
                db.add(log)
                await db.commit()
                
                return UserResponse(
                    user_id=user.id,
                    username=user.username,
                    email=user.email
                )
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
        
        # Logging Routes
        @self.router.post("/logs", response_model=LogResponse)
        async def log_action(
            request: Request,
            log_data: LogCreate,
            db: AsyncSession = Depends(get_db)
        ):
            try:
                # Create log
                log = Log(
                    user_id=log_data.user_id,
                    service=log_data.service,
                    action=log_data.action,
                    status=log_data.status
                )
                db.add(log)
                await db.commit()
                await db.refresh(log)
                
                # Log request
                log_request(
                    endpoint="/logs",
                    method="POST",
                    status_code=200,
                    user_id=str(log_data.user_id)
                )
                
                return LogResponse(
                    log_id=log.id,
                    timestamp=log.timestamp
                )
                
            except Exception as e:
                await db.rollback()
                log_error("/logs", e, str(log_data.user_id))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create log entry"
                )
        
        # Health Check Route
        @self.router.get("/health")
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

# Create router instance
shared_router = SharedServiceRouter().router 