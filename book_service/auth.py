from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import httpx
import os

security = HTTPBasic()
SHARED_SERVICE_URL = os.getenv("SHARED_SERVICE_URL", "http://localhost:8000")

async def verify_auth(credentials: HTTPBasicCredentials = Depends(security)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SHARED_SERVICE_URL}/auth/login",
            auth=(credentials.username, credentials.password)
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        return response.json()["user_id"] 