import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, MagicMock, patch
from models import User, Log  # Added Log for register tests
from schemas import UserResponse
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from routes import get_db, log_request, log_error, verify_credentials

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}
    
def test_register_user_success(client):
    # Mock the database session
    mock_db_session = AsyncMock()
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[log_request] = lambda: mock_db_session
    app.dependency_overrides[log_error] = lambda: mock_db_session

    # Mock user object that will be "created"
    mock_user = User(id=1, username="testuser", email="test@example.com")


    async def mock_refresh(instance):
        if isinstance(instance, User):
            instance.id = mock_user.id  # Ensure the instance gets an ID
        pass

    mock_db_session.refresh = AsyncMock(side_effect=mock_refresh)
    

    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    })

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["username"] == "testuser"
    assert response_data["email"] == "test@example.com"
    assert "user_id" in response_data

    assert mock_db_session.commit.call_count == 2  # For User and Log
    assert mock_db_session.refresh.call_count == 1  # For User

def test_register_user_already_exists(client):
    # Mock the database session
    mock_db_session = AsyncMock()
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[log_request] = lambda: mock_db_session
    app.dependency_overrides[log_error] = lambda: mock_db_session

    # Configure the commit mock to raise IntegrityError
    mock_db_session.commit = AsyncMock(side_effect=IntegrityError("mock error", params={}, orig=None))
    mock_db_session.rollback = AsyncMock()

    response = client.post("/api/v1/auth/register", json={
        "username": "existinguser",
        "email": "existing@example.com",
        "password": "testpassword"
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "Username or email already exists"
    
    mock_db_session.add.assert_called_once()  # For User
    mock_db_session.commit.assert_called_once()  # Attempted for User
    mock_db_session.rollback.assert_called_once()


def test_login_success(client):
    mock_db_session = AsyncMock()
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[log_request] = lambda: mock_db_session
    app.dependency_overrides[log_error] = lambda: mock_db_session

    mock_user = User(id=1, username="testuser", email="test@example.com")

    with patch('routes.verify_credentials', AsyncMock(return_value=mock_user)) as mock_verify_user:
        response = client.post("/api/v1/auth/login", 
                               auth=("testuser", "testpassword")
                            )

        assert response.status_code == 200
        response_data = response.json()
        user_response = UserResponse(**response_data) #to validate if the response is valid
        assert response_data["user_id"] == mock_user.id
        assert response_data["username"] == mock_user.username
        assert response_data["email"] == mock_user.email

def test_login_invalid_credentials(client):
    mock_db_session = AsyncMock()
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[log_request] = lambda: mock_db_session
    app.dependency_overrides[log_error] = lambda: mock_db_session

    # Capture the mock object for verify_credentials
    with patch('routes.verify_credentials', AsyncMock(side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"))) as mock_verify_user:
        response = client.post("/api/v1/auth/login", 
                               auth=("wronguser", "wrongpassword")
                            )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "User not found"
