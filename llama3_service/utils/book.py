import os
import httpx
from fastapi import HTTPException, status
from utils.logging import logger

BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://localhost:8001")

async def verify_book_exists(book_id: int, auth: tuple) -> bool:
    """
    Verify if a book exists in the book service.
    
    Args:
        book_id: The ID of the book to verify
        auth: Tuple of (username, password) for authentication
        
    Returns:
        bool: True if book exists, False otherwise
        
    Raises:
        HTTPException: If the book service is unavailable or returns an error
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BOOK_SERVICE_URL}/api/v1/books/{book_id}",
                auth=auth
            )
            
            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                return False
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed with book service"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Book service error: {response.text}"
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Book service is unavailable"
        ) 