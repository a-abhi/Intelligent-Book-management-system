from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
from models import Review
from schemas import ReviewCreate, ReviewResponse
from db import get_db
from auth import verify_auth
from logging_utils import log_action
from book_utils import verify_book_exists
from sqlalchemy import select

router = APIRouter()
security = HTTPBasic()

@router.post("/books/{book_id}/reviews", response_model=ReviewResponse)
async def create_review(
    book_id: int,
    review: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(verify_auth),
    credentials: HTTPBasicCredentials = Depends(security)
):
    try:
        # Verify book exists with authentication
        await verify_book_exists(str(book_id), (credentials.username, credentials.password))
        
        # Create review
        db_review = Review(
            book_id=book_id,
            user_id=user_id,
            rating=review.rating,
            text=review.text
        )
        db.add(db_review)
        await db.commit()
        await db.refresh(db_review)
        
        # Log success
        await log_action(str(user_id), "create_review", "success", f"Created review for book {book_id}")
        return db_review
        
    except ValueError as e:
        await log_action(str(user_id), "create_review", "error", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await log_action(str(user_id), "create_review", "error", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the review"
        )

@router.get("/books/{book_id}/reviews", response_model=List[ReviewResponse])
async def get_reviews(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(verify_auth),
    credentials: HTTPBasicCredentials = Depends(security)
):
    try:
        # Verify book exists with authentication
        await verify_book_exists(str(book_id), (credentials.username, credentials.password))
        
        # Get reviews
        stmt = select(Review).where(Review.book_id == book_id)
        result = await db.execute(stmt)
        reviews = result.scalars().all()
        
        # Log success
        await log_action(str(user_id), "get_reviews", "success", f"Retrieved reviews for book {book_id}")
        return reviews
        
    except ValueError as e:
        await log_action(str(user_id), "get_reviews", "error", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await log_action(str(user_id), "get_reviews", "error", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving reviews"
        )

@router.get("/health")
async def health_check():
    return {"status": "healthy"} 