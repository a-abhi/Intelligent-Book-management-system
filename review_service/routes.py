from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models import Review
from schemas import (BookReviewsSummary, ReviewCreate, ReviewResponse)
from utils.auth import verify_auth
from utils.book import verify_book_exists
from utils.logging import log_action, logger
from utils.review import generate_book_reviews_summary


class ReviewServiceRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1", tags=["reviews"])
        self.security = HTTPBasic()
        self._setup_routes()

    def _setup_routes(self):
        @self.router.post("/books/{book_id}/reviews", response_model=ReviewResponse)
        async def create_review(
            book_id: int,
            review: ReviewCreate,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth),
            credentials: HTTPBasicCredentials = Depends(self.security),
        ):
            try:
                # Verify book exists with authentication
                await verify_book_exists(
                    str(book_id), (credentials.username, credentials.password)
                )

                # Create review
                db_review = Review(
                    book_id=book_id,
                    user_id=user_id,
                    rating=review.rating,
                    comment=review.comment,
                )
                db.add(db_review)
                await db.commit()
                await db.refresh(db_review)

                # Log success
                await log_action(
                    str(user_id),
                    "create_review",
                    "success",
                    f"Created review for book {book_id}",
                )
                return db_review

            except HTTPException:
                raise
            except ValueError as e:
                await log_action(str(user_id), "create_review", "error", str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )
            except Exception as e:
                await log_action(str(user_id), "create_review", "error", str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while creating the review",
                )

        @self.router.get(
            "/books/{book_id}/reviews", response_model=List[ReviewResponse]
        )
        async def get_reviews(
            book_id: int,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth),
            credentials: HTTPBasicCredentials = Depends(self.security),
        ):
            try:
                # Verify book exists with authentication
                await verify_book_exists(
                    str(book_id), (credentials.username, credentials.password)
                )

                # Get reviews
                stmt = select(Review).where(Review.book_id == book_id)
                result = await db.execute(stmt)
                reviews = result.scalars().all()

                # Log success
                await log_action(
                    str(user_id),
                    "get_reviews",
                    "success",
                    f"Retrieved reviews for book {book_id}",
                )
                return reviews

            except HTTPException:
                # Propagate the original error from book_utils
                raise
            except ValueError as e:
                await log_action(str(user_id), "get_reviews", "error", str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )
            except Exception as e:
                await log_action(str(user_id), "get_reviews", "error", str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while retrieving reviews",
                )

        @self.router.get(
            "/books/{book_id}/reviews/summary", response_model=BookReviewsSummary
        )
        async def get_book_reviews_summary(
            book_id: int,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth),
            credentials: HTTPBasicCredentials = Depends(self.security),
        ):
            """
            Generate a summary of all reviews for a book using AI.
            """
            try:
                # Verify book exists with authentication
                try:
                    await verify_book_exists(
                        str(book_id), (credentials.username, credentials.password)
                    )
                except HTTPException as e:
                    if e.status_code == status.HTTP_404_NOT_FOUND:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Book with ID {book_id} not found",
                        )
                    elif e.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Book service is currently unavailable. Please try again later.",
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error verifying book existence",
                        )

                # Get all reviews for the book
                stmt = select(Review).where(Review.book_id == book_id)
                result = await db.execute(stmt)
                reviews = result.scalars().all()

                if not reviews:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No reviews found for book with ID {book_id}",
                    )

                # Generate summary
                summary = await generate_book_reviews_summary(
                    reviews=reviews, auth=(credentials.username, credentials.password)
                )

                # Calculate average rating
                avg_rating = sum(r.rating for r in reviews) / len(reviews)

                await log_action(
                    user_id=str(user_id),
                    action="get_book_reviews_summary",
                    status="success",
                    details=f"Generated summary for book {book_id}",
                )

                return BookReviewsSummary(
                    book_id=book_id,
                    summary=summary,
                    average_rating=avg_rating,
                    total_reviews=len(reviews),
                )

            except HTTPException:
                raise
            except Exception as e:
                await log_action(
                    user_id=str(user_id),
                    action="get_book_reviews_summary",
                    status="error",
                    details=str(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while generating the summary",
                )

        @self.router.get("/health")
        async def health_check():
            try:
                logger.info("Health check requested")
                return {"status": "healthy"}
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Service is unhealthy")


# Create router instance
review_router = ReviewServiceRouter().router
