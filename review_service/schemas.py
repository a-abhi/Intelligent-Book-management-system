import uuid
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class ReviewBase(BaseModel):
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating must be between 1 and 5",
        error_messages={
            "ge": "Rating must be at least 1",
            "le": "Rating cannot be more than 5"
        }
    )
    text: Optional[str] = None

    @validator('rating')
    def validate_rating(cls, v):
        if not isinstance(v, int):
            raise ValueError('Rating must be an integer')
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

class ReviewCreate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    id: int
    book_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 