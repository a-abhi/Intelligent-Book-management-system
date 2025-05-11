from datetime import datetime

from pydantic import BaseModel, Field


class BookSummaryBase(BaseModel):
    book_id: int = Field(..., description="ID of the book to summarize")
    content: str = Field(
        ..., min_length=1, description="Content of the book to summarize"
    )


class BookSummaryCreate(BookSummaryBase):
    pass


class BookSummaryResponse(BookSummaryBase):
    id: int = Field(..., description="Unique identifier for the summary")
    summary: str = Field(..., description="AI-generated summary of the book")
    created_at: datetime = Field(
        ..., description="Timestamp when the summary was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the summary was last updated"
    )

    class Config:
        from_attributes = True


class ReviewSummaryRequest(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    content: str = Field(..., description="Reviews content to summarize")


class ReviewSummaryResponse(BaseModel):
    book_id: int = Field(..., description="ID of the book")
    summary: str = Field(..., description="Generated summary of reviews")

    class Config:
        from_attributes = True
