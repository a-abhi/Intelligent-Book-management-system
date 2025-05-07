import httpx
import os
from fastapi import HTTPException, status

BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://localhost:8001")

async def get_books_by_genre(genre: str, credentials: tuple = None) -> list:
    """
    Get books by genre from the book service.
    
    Args:
        genre: The genre to filter books by
        credentials: Optional tuple of (username, password) for basic auth
        
    Returns:
        List of books matching the genre
        
    Raises:
        HTTPException: If there's an error communicating with the book service
    """
    try:
        auth = None
        if credentials:
            auth = httpx.BasicAuth(credentials[0], credentials[1])
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BOOK_SERVICE_URL}/books",
                params={"genre": genre},
                auth=auth
            )
            
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed with book service"
                )
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error communicating with book service: {response.text}"
                )
                
            return response.json()
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Book service is unavailable: {str(e)}"
        )

async def get_all_books():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BOOK_SERVICE_URL}/books")
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch books")
        return response.json() 