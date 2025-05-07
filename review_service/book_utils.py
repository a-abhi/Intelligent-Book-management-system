import httpx
import os
from fastapi import HTTPException, status
from auth import verify_auth
from logging_utils import logger

BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://localhost:8001")

async def verify_book_exists(book_id: str, credentials: tuple = None):
    """
    Verify if a book exists in the book service.
    
    Args:
        book_id: The ID of the book to verify
        credentials: Tuple of (username, password) for authentication
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BOOK_SERVICE_URL}/books/{book_id}",
                auth=credentials
            )
            
            # Pass through the original response status and text
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text
                )
                
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Book service is unavailable: {str(e)}"
        ) 