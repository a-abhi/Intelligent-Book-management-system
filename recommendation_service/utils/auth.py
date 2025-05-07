from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import httpx
import os

SHARED_SERVICE_URL = os.getenv("SHARED_SERVICE_URL", "http://localhost:8000")
security = HTTPBasic()

async def verify_auth(credentials: HTTPBasicCredentials = Depends(security)) -> int:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SHARED_SERVICE_URL}/api/v1/auth/login",
                auth=(credentials.username, credentials.password)
            )
            
            if response.status_code == 200:
                return response.json()["user_id"]
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable"
        ) 