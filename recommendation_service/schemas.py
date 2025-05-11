from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PreferenceBase(BaseModel):
    genre: str = Field(..., min_length=1, description="Genre of the book")


class PreferenceCreate(PreferenceBase):
    pass


class PreferenceResponse(PreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookRecommendation(BaseModel):
    id: int
    title: str
    author: Optional[str] = None
    genre: Optional[str] = None
    year_published: Optional[int] = None
    summary: Optional[str] = None

    class Config:
        from_attributes = True
