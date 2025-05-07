from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
from models import User
from db import get_db

security = HTTPBasic()

async def verify_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Use select statement to query user
        stmt = select(User).where(User.username == credentials.username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Basic"},
            )
            
        if not secrets.compare_digest(user.password, credentials.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password",
                headers={"WWW-Authenticate": "Basic"},
            )
            
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        ) 