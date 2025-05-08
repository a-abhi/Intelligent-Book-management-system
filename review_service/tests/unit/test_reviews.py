import pytest
from fastapi import HTTPException
from models.reviews import Review
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_review_success(test_db, sample_review_data):
    """Test successful review creation."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    async with async_session() as session:
        review = Review(**sample_review_data)
        session.add(review)
        await session.commit()
        await session.refresh(review)
        
        assert review.id is not None
        assert review.book_id == sample_review_data["book_id"]
        assert review.rating == sample_review_data["rating"]
        assert review.comment == sample_review_data["comment"]
        assert review.user_id == sample_review_data["user_id"]

@pytest.mark.asyncio
async def test_get_review_by_id_success(test_db, sample_review_data):
    """Test getting a review by ID."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create a test review
    async with async_session() as session:
        review = Review(**sample_review_data)
        session.add(review)
        await session.commit()
        await session.refresh(review)
        
        # Test getting the review
        stmt = select(Review).where(Review.id == review.id)
        result = await session.execute(stmt)
        retrieved_review = result.scalar_one_or_none()
        
        assert retrieved_review is not None
        assert retrieved_review.id == review.id
        assert retrieved_review.book_id == sample_review_data["book_id"]
        assert retrieved_review.rating == sample_review_data["rating"]

@pytest.mark.asyncio
async def test_get_review_by_id_not_found(test_db):
    """Test getting a non-existent review."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    async with async_session() as session:
        stmt = select(Review).where(Review.id == 999)
        result = await session.execute(stmt)
        review = result.scalar_one_or_none()
        
        assert review is None

@pytest.mark.asyncio
async def test_update_review_success(test_db, sample_review_data):
    """Test successful review update."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create a test review
    async with async_session() as session:
        review = Review(**sample_review_data)
        session.add(review)
        await session.commit()
        await session.refresh(review)
        
        # Update the review
        update_data = {"rating": 5, "comment": "Updated review comment"}
        for key, value in update_data.items():
            setattr(review, key, value)
        await session.commit()
        await session.refresh(review)
        
        assert review.rating == 5
        assert review.comment == "Updated review comment"
        assert review.book_id == sample_review_data["book_id"]  # Unchanged field

@pytest.mark.asyncio
async def test_delete_review_success(test_db, sample_review_data):
    """Test successful review deletion."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create a test review
    async with async_session() as session:
        review = Review(**sample_review_data)
        session.add(review)
        await session.commit()
        await session.refresh(review)
        
        # Delete the review
        await session.delete(review)
        await session.commit()
        
        # Verify deletion
        stmt = select(Review).where(Review.id == review.id)
        result = await session.execute(stmt)
        deleted_review = result.scalar_one_or_none()
        
        assert deleted_review is None

@pytest.mark.asyncio
async def test_get_book_reviews_success(test_db, sample_review_data):
    """Test getting all reviews for a book."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create test reviews
    async with async_session() as session:
        reviews = [
            Review(**sample_review_data),
            Review(**{**sample_review_data, "rating": 3, "comment": "Another review"})
        ]
        for review in reviews:
            session.add(review)
        await session.commit()
        
        # Get reviews for the book
        stmt = select(Review).where(Review.book_id == sample_review_data["book_id"])
        result = await session.execute(stmt)
        book_reviews = result.scalars().all()
        
        assert len(book_reviews) == 2
        assert all(review.book_id == sample_review_data["book_id"] for review in book_reviews) 