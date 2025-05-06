from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Text, DateTime
from datetime import datetime

Base = declarative_base()

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    author = Column(String)
    genre = Column(String)
    year_published = Column(Integer)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 