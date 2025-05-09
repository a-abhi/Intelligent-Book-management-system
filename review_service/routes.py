from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from models import Review
from schemas import ReviewCreate, ReviewResponse, BookReviewsSummary, ReviewSummaryRequest
from db import get_db
from utils.auth import verify_auth
from utils.logging import log_action, logger
from utils.review import generate_review_summary

class ReviewServiceRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1", tags=["reviews"])
        self.security = HTTPBasic()
        self._setup_routes()
    
    def _setup_routes(self):
        @self.router.post("/reviews", response_model=ReviewResponse)
        async def create_review(
            review: ReviewCreate,
            book_id: int,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth),
            credentials: HTTPBasicCredentials = Depends(self.security)
        ):
            try:
                logger.info(f"Attempting to create review for book {book_id}")
                
                # Create review
                db_review = Review(
                    book_id=book_id,
                    user_id=user_id,
                    rating=review.rating,
                    comment=review.comment
                )
                db.add(db_review)
                await db.commit()
                await db.refresh(db_review)
                
                # Generate summary if comment is provided
                if review.comment:
                    try:
                        generated_summary = await generate_review_summary(
                            review_id=db_review.id,
                            content=review.comment,
                            auth=(credentials.username, credentials.password)
                        )
                        # Store summary in a separate table or update the review
                        # This depends on your implementation of generate_review_summary
                    except Exception as e:
                        logger.warning(f"Failed to generate summary: {str(e)}")
                        # Continue without summary - don't fail the review creation
                
                logger.info(f"Successfully created review with ID: {db_review.id}")
                await log_action(
                    db=db,
                    user_id=user_id,
                    action="create_review",
                    status="success",
                    details=f"Created review for book {book_id}"
                )
                return db_review
                
            except IntegrityError as e:
                await db.rollback()
                error_msg = f"Database integrity error while creating review: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action="create_review",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=400,
                    detail="A review with this information already exists"
                )
            except Exception as e:
                await db.rollback()
                error_msg = f"Error creating review: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action="create_review",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error creating review: {str(e)}"
                )

        @self.router.get("/reviews", response_model=List[ReviewResponse])
        async def get_reviews(
            book_id: Optional[int] = None,
            user_id: Optional[int] = None,
            db: AsyncSession = Depends(get_db),
            current_user_id: int = Depends(verify_auth)
        ):
            try:
                logger.info(f"Attempting to fetch reviews with filters: book_id={book_id}, user_id={user_id}")
                
                # Build query based on filters
                stmt = select(Review)
                if book_id:
                    stmt = stmt.where(Review.book_id == book_id)
                if user_id:
                    stmt = stmt.where(Review.user_id == user_id)
                
                result = await db.execute(stmt)
                reviews = result.scalars().all()
                
                logger.info(f"Successfully fetched {len(reviews)} reviews")
                await log_action(
                    db=db,
                    user_id=current_user_id,
                    action="get_reviews",
                    status="success",
                    details=f"Retrieved {len(reviews)} reviews"
                )
                return reviews
                
            except Exception as e:
                error_msg = f"Error fetching reviews: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=current_user_id,
                    action="get_reviews",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error fetching reviews: {str(e)}"
                )

        @self.router.get("/reviews/{review_id}", response_model=ReviewResponse)
        async def get_review(
            review_id: int,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth)
        ):
            try:
                logger.info(f"Attempting to fetch review with ID: {review_id}")
                
                stmt = select(Review).where(Review.id == review_id)
                result = await db.execute(stmt)
                review = result.scalar_one_or_none()
                
                if not review:
                    error_msg = f"Review not found with ID: {review_id}"
                    logger.warning(error_msg)
                    await log_action(
                        db=db,
                        user_id=user_id,
                        action=f"get_review_{review_id}",
                        status="failure",
                        details=error_msg
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"Review with ID {review_id} not found"
                    )
                    
                logger.info(f"Successfully found review: {review_id}")
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"get_review_{review_id}",
                    status="success",
                    details=f"Retrieved review {review_id}"
                )
                return review
                
            except HTTPException:
                raise
            except Exception as e:
                error_msg = f"Error fetching review {review_id}: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"get_review_{review_id}",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error fetching review: {str(e)}"
                )

        @self.router.put("/reviews/{review_id}", response_model=ReviewResponse)
        async def update_review(
            review_id: int,
            review: ReviewCreate,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth),
            credentials: HTTPBasicCredentials = Depends(self.security)
        ):
            try:
                logger.info(f"Attempting to update review with ID: {review_id}")
                
                stmt = select(Review).where(Review.id == review_id)
                result = await db.execute(stmt)
                db_review = result.scalar_one_or_none()
                
                if not db_review:
                    error_msg = f"Review not found with ID: {review_id}"
                    logger.warning(error_msg)
                    await log_action(
                        db=db,
                        user_id=user_id,
                        action=f"update_review_{review_id}",
                        status="failure",
                        details=error_msg
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"Review with ID {review_id} not found"
                    )
                
                # Check if user owns the review
                if db_review.user_id != user_id:
                    error_msg = f"User {user_id} not authorized to update review {review_id}"
                    logger.warning(error_msg)
                    await log_action(
                        db=db,
                        user_id=user_id,
                        action=f"update_review_{review_id}",
                        status="failure",
                        details=error_msg
                    )
                    raise HTTPException(
                        status_code=403,
                        detail="Not authorized to update this review"
                    )
                
                # Update review fields
                for key, value in review.dict().items():
                    setattr(db_review, key, value)
                
                # Generate new summary if comment is provided
                if review.comment:
                    try:
                        generated_summary = await generate_review_summary(
                            review_id=db_review.id,
                            content=review.comment,
                            auth=(credentials.username, credentials.password)
                        )
                        # Update summary in database
                    except Exception as e:
                        logger.warning(f"Failed to generate summary: {str(e)}")
                        # Continue without summary update
                
                await db.commit()
                await db.refresh(db_review)
                
                logger.info(f"Successfully updated review: {review_id}")
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"update_review_{review_id}",
                    status="success",
                    details=f"Updated review {review_id}"
                )
                return db_review
                
            except HTTPException:
                raise
            except Exception as e:
                await db.rollback()
                error_msg = f"Error updating review {review_id}: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"update_review_{review_id}",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error updating review: {str(e)}"
                )

        @self.router.delete("/reviews/{review_id}")
        async def delete_review(
            review_id: int,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth)
        ):
            try:
                logger.info(f"Attempting to delete review with ID: {review_id}")
                
                stmt = select(Review).where(Review.id == review_id)
                result = await db.execute(stmt)
                review = result.scalar_one_or_none()
                
                if not review:
                    error_msg = f"Review not found with ID: {review_id}"
                    logger.warning(error_msg)
                    await log_action(
                        db=db,
                        user_id=user_id,
                        action=f"delete_review_{review_id}",
                        status="failure",
                        details=error_msg
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"Review with ID {review_id} not found"
                    )
                
                # Check if user owns the review
                if review.user_id != user_id:
                    error_msg = f"User {user_id} not authorized to delete review {review_id}"
                    logger.warning(error_msg)
                    await log_action(
                        db=db,
                        user_id=user_id,
                        action=f"delete_review_{review_id}",
                        status="failure",
                        details=error_msg
                    )
                    raise HTTPException(
                        status_code=403,
                        detail="Not authorized to delete this review"
                    )
                
                await db.delete(review)
                await db.commit()
                
                logger.info(f"Successfully deleted review: {review_id}")
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"delete_review_{review_id}",
                    status="success",
                    details=f"Deleted review {review_id}"
                )
                return {"message": f"Review {review_id} deleted successfully"}
                
            except HTTPException:
                raise
            except Exception as e:
                await db.rollback()
                error_msg = f"Error deleting review {review_id}: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"delete_review_{review_id}",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error deleting review: {str(e)}"
                )

        @self.router.get("/books/{book_id}/reviews/summary", response_model=BookReviewsSummary)
        async def get_book_reviews_summary(
            book_id: int,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth)
        ):
            try:
                logger.info(f"Attempting to get reviews summary for book: {book_id}")
                
                # Get average rating and total reviews
                stmt = select(
                    func.avg(Review.rating).label("average_rating"),
                    func.count(Review.id).label("total_reviews")
                ).where(Review.book_id == book_id)
                
                result = await db.execute(stmt)
                summary_data = result.first()
                
                if not summary_data or not summary_data.total_reviews:
                    error_msg = f"No reviews found for book {book_id}"
                    logger.warning(error_msg)
                    await log_action(
                        db=db,
                        user_id=user_id,
                        action=f"get_book_reviews_summary_{book_id}",
                        status="failure",
                        details=error_msg
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"No reviews found for book {book_id}"
                    )
                
                # Get all reviews for the book
                stmt = select(Review).where(Review.book_id == book_id)
                result = await db.execute(stmt)
                reviews = result.scalars().all()
                
                # Generate summary from all reviews
                all_comments = " ".join([r.comment for r in reviews if r.comment])
                
                return BookReviewsSummary(
                    book_id=book_id,
                    summary=all_comments[:500] + "..." if len(all_comments) > 500 else all_comments,
                    average_rating=float(summary_data.average_rating),
                    total_reviews=summary_data.total_reviews
                )
                
            except HTTPException:
                raise
            except Exception as e:
                error_msg = f"Error getting reviews summary for book {book_id}: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"get_book_reviews_summary_{book_id}",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error getting reviews summary: {str(e)}"
                )

        @self.router.get("/health")
        async def health_check():
            try:
                logger.info("Health check requested")
                return {"status": "healthy"}
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Service is unhealthy"
                )

# Create router instance
review_router = ReviewServiceRouter().router 