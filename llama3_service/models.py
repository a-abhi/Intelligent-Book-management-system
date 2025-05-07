from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from datetime import datetime
from db import Base

class BookSummary(Base):
    __tablename__ = 'book_summaries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)  # Store original content
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_book_summaries_book_id', 'book_id'),
        Index('idx_book_summaries_user_id', 'user_id'),
        # Ensure each user has only one summary per book
        Index('idx_book_summaries_unique', 'book_id', 'user_id', unique=True),
    ) 