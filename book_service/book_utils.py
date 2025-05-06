import httpx
import os
from fastapi import HTTPException, status

LLAMA3_SERVICE_URL = os.getenv("LLAMA3_SERVICE_URL", "http://localhost:8003")

async def generate_book_summary(book_id: int, content: str, auth: tuple) -> str:
    """
    Call the LLaMA3 service to generate a summary for a book.
    
    Args:
        book_id: ID of the book
        content: Content of the book to summarize
        auth: Tuple of (username, password) for authentication
        
    Returns:
        Generated summary
        
    Raises:
        HTTPException: If the LLaMA3 service call fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLAMA3_SERVICE_URL}/api/v1/generate-summary",
                json={
                    "book_id": book_id,
                    "content": content
                },
                auth=auth
            )
            
            if response.status_code == 200:
                return response.json()["summary"]
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed with LLaMA3 service"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error generating summary"
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLaMA3 service is unavailable"
        ) 