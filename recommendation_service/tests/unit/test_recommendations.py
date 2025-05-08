import pytest
from fastapi import HTTPException
from models.recommendations import Recommendation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_recommendation_success(test_db, sample_recommendation_data):
    """Test successful recommendation creation."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    async with async_session() as session:
        recommendation = Recommendation(**sample_recommendation_data)
        session.add(recommendation)
        await session.commit()
        await session.refresh(recommendation)
        
        assert recommendation.id is not None
        assert recommendation.book_id == sample_recommendation_data["book_id"]
        assert recommendation.user_id == sample_recommendation_data["user_id"]
        assert recommendation.score == sample_recommendation_data["score"]
        assert recommendation.reason == sample_recommendation_data["reason"]

@pytest.mark.asyncio
async def test_get_recommendation_by_id_success(test_db, sample_recommendation_data):
    """Test getting a recommendation by ID."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create a test recommendation
    async with async_session() as session:
        recommendation = Recommendation(**sample_recommendation_data)
        session.add(recommendation)
        await session.commit()
        await session.refresh(recommendation)
        
        # Test getting the recommendation
        stmt = select(Recommendation).where(Recommendation.id == recommendation.id)
        result = await session.execute(stmt)
        retrieved_recommendation = result.scalar_one_or_none()
        
        assert retrieved_recommendation is not None
        assert retrieved_recommendation.id == recommendation.id
        assert retrieved_recommendation.book_id == sample_recommendation_data["book_id"]
        assert retrieved_recommendation.score == sample_recommendation_data["score"]

@pytest.mark.asyncio
async def test_get_recommendation_by_id_not_found(test_db):
    """Test getting a non-existent recommendation."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    async with async_session() as session:
        stmt = select(Recommendation).where(Recommendation.id == 999)
        result = await session.execute(stmt)
        recommendation = result.scalar_one_or_none()
        
        assert recommendation is None

@pytest.mark.asyncio
async def test_update_recommendation_success(test_db, sample_recommendation_data):
    """Test successful recommendation update."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create a test recommendation
    async with async_session() as session:
        recommendation = Recommendation(**sample_recommendation_data)
        session.add(recommendation)
        await session.commit()
        await session.refresh(recommendation)
        
        # Update the recommendation
        update_data = {"score": 0.95, "reason": "Updated recommendation reason"}
        for key, value in update_data.items():
            setattr(recommendation, key, value)
        await session.commit()
        await session.refresh(recommendation)
        
        assert recommendation.score == 0.95
        assert recommendation.reason == "Updated recommendation reason"
        assert recommendation.book_id == sample_recommendation_data["book_id"]  # Unchanged field

@pytest.mark.asyncio
async def test_delete_recommendation_success(test_db, sample_recommendation_data):
    """Test successful recommendation deletion."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create a test recommendation
    async with async_session() as session:
        recommendation = Recommendation(**sample_recommendation_data)
        session.add(recommendation)
        await session.commit()
        await session.refresh(recommendation)
        
        # Delete the recommendation
        await session.delete(recommendation)
        await session.commit()
        
        # Verify deletion
        stmt = select(Recommendation).where(Recommendation.id == recommendation.id)
        result = await session.execute(stmt)
        deleted_recommendation = result.scalar_one_or_none()
        
        assert deleted_recommendation is None

@pytest.mark.asyncio
async def test_get_user_recommendations_success(test_db, sample_recommendation_data):
    """Test getting all recommendations for a user."""
    engine, async_session, init_test_db = test_db
    await init_test_db()
    
    # Create test recommendations
    async with async_session() as session:
        recommendations = [
            Recommendation(**sample_recommendation_data),
            Recommendation(**{**sample_recommendation_data, "book_id": 2, "score": 0.75})
        ]
        for recommendation in recommendations:
            session.add(recommendation)
        await session.commit()
        
        # Get recommendations for the user
        stmt = select(Recommendation).where(Recommendation.user_id == sample_recommendation_data["user_id"])
        result = await session.execute(stmt)
        user_recommendations = result.scalars().all()
        
        assert len(user_recommendations) == 2
        assert all(rec.user_id == sample_recommendation_data["user_id"] for rec in user_recommendations) 