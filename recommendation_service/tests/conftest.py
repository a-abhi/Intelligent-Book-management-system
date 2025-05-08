import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
from db.session import get_db
from models import Base
import os
from unittest.mock import AsyncMock, patch
import base64

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
def test_db():
    """Create a test database session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async def override_get_db():
        async with async_session() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async def init_test_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    return engine, async_session, init_test_db

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def mock_auth():
    """Create a mock authentication token."""
    credentials = base64.b64encode(b"test_user:test_password").decode()
    return credentials

@pytest.fixture
def mock_book_service():
    """Mock book service responses."""
    return {
        "get_book": AsyncMock(return_value={
            "id": 1,
            "title": "Test Book",
            "author": "Test Author",
            "description": "Test Description"
        })
    }

@pytest.fixture
def mock_review_service():
    """Mock review service responses."""
    return {
        "get_book_reviews": AsyncMock(return_value=[
            {
                "id": 1,
                "book_id": 1,
                "user_id": "test_user",
                "rating": 4,
                "comment": "Great book!"
            }
        ])
    }

@pytest.fixture
def sample_recommendation_data():
    """Sample recommendation data for testing."""
    return {
        "book_id": 1,
        "user_id": "test_user",
        "score": 0.85,
        "reason": "Based on your reading history and preferences"
    } 