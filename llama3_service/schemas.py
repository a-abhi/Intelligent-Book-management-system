from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MessageBase(BaseModel):
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    session_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatSessionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the chat session")

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionResponse(ChatSessionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's message to the AI")
    session_id: Optional[int] = Field(None, description="Existing session ID if continuing a conversation")

class ChatResponse(BaseModel):
    message: str = Field(..., description="AI's response message")
    session_id: int = Field(..., description="ID of the chat session")

class SummaryRequest(BaseModel):
    content: str

class SummaryResponse(BaseModel):
    summary: str

class BookSummaryBase(BaseModel):
    book_id: int = Field(..., description="ID of the book to summarize")
    content: str = Field(..., min_length=1, description="Content of the book to summarize")

class BookSummaryCreate(BookSummaryBase):
    pass

class BookSummaryResponse(BookSummaryBase):
    id: int = Field(..., description="Unique identifier for the summary")
    summary: str = Field(..., description="AI-generated summary of the book")
    created_at: datetime = Field(..., description="Timestamp when the summary was created")
    updated_at: datetime = Field(..., description="Timestamp when the summary was last updated")
    
    class Config:
        from_attributes = True 