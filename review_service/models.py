from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Index, Integer, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    rating = Column(Float, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_reviews_book_id", "book_id"),
        Index("idx_reviews_user_id", "user_id"),
    )
