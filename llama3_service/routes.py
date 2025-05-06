from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import BookSummary
from schemas import (
    BookSummaryCreate,
    BookSummaryResponse
)
from db import get_db
from auth import verify_auth
from logging_utils import log_action, logger
import httpx
import os
from typing import Optional

router = APIRouter()
security = HTTPBasic()

LLAMA_API_URL = os.getenv("LLAMA_API_URL", "http://localhost:11434")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "llama2")


async def get_cached_summary(
    db: AsyncSession,
    book_id: int,
    user_id: int,
    refresh: bool = False
) -> Optional[BookSummary]:
    """
    Get a cached summary for the given book_id and user_id if it exists.
    
    Args:
        db: Database session
        book_id: The ID of the book
        user_id: The ID of the user
        refresh: If True, skip cache and force regeneration
        
    Returns:
        Optional[BookSummary]: The cached summary if found, None otherwise
    """
    if refresh:
        return None
        
    stmt = select(BookSummary).where(
        BookSummary.book_id == book_id,
        BookSummary.user_id == user_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@router.post("/generate-summary", response_model=BookSummaryResponse)
async def generate_summary(
    request: BookSummaryCreate,
    refresh: bool = False,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(verify_auth),
    credentials: HTTPBasicCredentials = Depends(security)
):
    try:
        # Check if summary exists in database
        existing_summary = await get_cached_summary(db, request.book_id, user_id, refresh)
        
        if existing_summary and not refresh:
            await log_action(
                user_id=str(user_id),
                action="get_summary",
                status="success",
                details=f"Retrieved cached summary for book {request.book_id}"
            )
            return existing_summary
        
        # Generate new summary
        summary = await _generate_summary(request.content)
        
        if existing_summary:
            # Update existing summary
            existing_summary.summary = summary
            await db.commit()
            await db.refresh(existing_summary)
            
            await log_action(
                user_id=str(user_id),
                action="update_summary",
                status="success",
                details=f"Updated summary for book {request.book_id}"
            )
            return existing_summary
            
        # Create new summary
        db_summary = BookSummary(
            book_id=request.book_id,
            user_id=user_id,
            summary=summary
        )
        db.add(db_summary)
        await db.commit()
        await db.refresh(db_summary)
        
        await log_action(
            user_id=str(user_id),
            action="create_summary",
            status="success",
            details=f"Created summary for book {request.book_id}"
        )
        return db_summary
        
    except Exception as e:
        await log_action(
            user_id=str(user_id),
            action="generate_summary",
            status="error",
            details=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating summary"
        )

async def _generate_summary(content: str) -> str:
    """
    Generate a summary using the Llama model.
    
    Args:
        content: The content to summarize
        
    Returns:
        Generated summary
    """
    prompt = f"Please provide a concise summary of the following text:\n\n{content}"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LLAMA_API_URL}/api/generate",
            json={
                "model": LLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error getting AI response"
            )
        
        return response.json()["response"]

@router.get("/summaries/{book_id}", response_model=BookSummaryResponse)
async def get_summary(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(verify_auth)
):
    try:
        stmt = select(BookSummary).where(
            BookSummary.book_id == book_id,
            BookSummary.user_id == user_id
        )
        result = await db.execute(stmt)
        summary = result.scalar_one_or_none()
        
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summary not found"
            )
        
        await log_action(
            user_id=str(user_id),
            action="get_summary",
            status="success",
            details=f"Retrieved summary for book {book_id}"
        )
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        await log_action(
            user_id=str(user_id),
            action="get_summary",
            status="error",
            details=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the summary"
        )

@router.get("/health")
async def health_check():
    try:
        # Check if Llama API is available
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LLAMA_API_URL}/api/tags")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Llama API is not available"
                )
        
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not healthy"
        ) 