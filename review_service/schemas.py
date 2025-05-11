from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, confloat, validator


class ReviewBase(BaseModel):
    rating: confloat(ge=1.0, le=5.0) = Field(..., description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, description="Review comment")

    @validator("rating")
    def validate_rating(cls, v):
        if not isinstance(v, float):
            raise ValueError("Rating must be a float")
        if v < 1.0 or v > 5.0:
            raise ValueError("Rating must be between 1.0 and 5.0")
        return v


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(ReviewBase):
    id: int = Field(..., description="Unique identifier for the review")
    book_id: int = Field(..., description="ID of the book being reviewed")
    user_id: int = Field(..., description="ID of the user who wrote the review")
    created_at: datetime = Field(
        ..., description="Timestamp when the review was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the review was last updated"
    )

    class Config:
        from_attributes = True


class BookReviewsSummary(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    summary: str = Field(
        ..., description="AI-generated summary of all reviews for the book"
    )
    average_rating: float = Field(..., description="Average rating of all reviews")
    total_reviews: int = Field(..., description="Total number of reviews")


class ReviewSummaryRequest(BaseModel):
    review_id: int = Field(..., description="ID of the review to summarize")
