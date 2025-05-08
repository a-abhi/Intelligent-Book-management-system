import pytest
from fastapi import HTTPException
from models import Book
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

@pytest.mark.asyncio
async def test_create_book_success(test_db, sample_book_data):
    """Test successful book creation."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    async with async_session() as session:
        book = Book(**sample_book_data)
        session.add(book)
        await session.commit()
        await session.refresh(book)
        
        assert book.id is not None
        assert book.title == sample_book_data["title"]
        assert book.author == sample_book_data["author"]
        assert book.genre == sample_book_data["genre"]
        assert book.year_published == sample_book_data["year_published"]
        assert book.summary == sample_book_data["summary"]
        assert isinstance(book.created_at, datetime)
        assert isinstance(book.updated_at, datetime)

@pytest.mark.asyncio
async def test_get_book_by_id_success(test_db, sample_book_data):
    """Test getting a book by ID."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create a test book
    async with async_session() as session:
        book = Book(**sample_book_data)
        session.add(book)
        await session.commit()
        await session.refresh(book)
        
        # Test getting the book
        stmt = select(Book).where(Book.id == book.id)
        result = await session.execute(stmt)
        retrieved_book = result.scalar_one_or_none()
        
        assert retrieved_book is not None
        assert retrieved_book.id == book.id
        assert retrieved_book.title == sample_book_data["title"]
        assert retrieved_book.author == sample_book_data["author"]
        assert retrieved_book.genre == sample_book_data["genre"]
        assert retrieved_book.year_published == sample_book_data["year_published"]
        assert retrieved_book.summary == sample_book_data["summary"]

@pytest.mark.asyncio
async def test_get_book_by_id_not_found(test_db):
    """Test getting a non-existent book."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    async with async_session() as session:
        stmt = select(Book).where(Book.id == 999)
        result = await session.execute(stmt)
        book = result.scalar_one_or_none()
        
        assert book is None

@pytest.mark.asyncio
async def test_update_book_success(test_db, sample_book_data):
    """Test successful book update."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create a test book
    async with async_session() as session:
        book = Book(**sample_book_data)
        session.add(book)
        await session.commit()
        await session.refresh(book)
        
        # Update the book
        update_data = {
            "title": "Updated Title",
            "author": "Updated Author",
            "genre": "Updated Genre",
            "year_published": 2025,
            "summary": "Updated summary"
        }
        for key, value in update_data.items():
            setattr(book, key, value)
        await session.commit()
        await session.refresh(book)
        
        assert book.title == "Updated Title"
        assert book.author == "Updated Author"
        assert book.genre == "Updated Genre"
        assert book.year_published == 2025
        assert book.summary == "Updated summary"

@pytest.mark.asyncio
async def test_delete_book_success(test_db, sample_book_data):
    """Test successful book deletion."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create a test book
    async with async_session() as session:
        book = Book(**sample_book_data)
        session.add(book)
        await session.commit()
        await session.refresh(book)
        
        # Delete the book
        await session.delete(book)
        await session.commit()
        
        # Verify deletion
        stmt = select(Book).where(Book.id == book.id)
        result = await session.execute(stmt)
        deleted_book = result.scalar_one_or_none()
        
        assert deleted_book is None

@pytest.mark.asyncio
async def test_search_books_success(test_db, sample_book_data):
    """Test successful book search."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create test books
    async with async_session() as session:
        books = [
            Book(**sample_book_data),
            Book(**{**sample_book_data, "title": "Another Book"})
        ]
        for book in books:
            session.add(book)
        await session.commit()
        
        # Search by title
        stmt = select(Book).where(Book.title.ilike("%Test%"))
        result = await session.execute(stmt)
        found_books = result.scalars().all()
        
        assert len(found_books) == 1
        assert found_books[0].title == sample_book_data["title"] 