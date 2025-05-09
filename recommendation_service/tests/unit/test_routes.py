from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from main import app
from schemas import PreferenceResponse, BookRecommendation
from models import Preference
from routes import get_db, verify_auth

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_recommendations_success():
    # 1. Mock dependencies
    mock_db_session = AsyncMock()
    mock_user_id = 123

    # Configure the mock_db_session
    mock_db_session.execute = AsyncMock()

    # 2. Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    # 3. Mock preferences and book service response
    mock_preferences = [
        Preference(id=1, user_id=mock_user_id, genre="Fiction"),
        Preference(id=2, user_id=mock_user_id, genre="Science")
    ]

    mock_books = [
        {"id": 1, "title": "Book 1", "author": "Author 1", "genre": "Fiction"},
        {"id": 2, "title": "Book 2", "author": "Author 2", "genre": "Science"}
    ]

    # Mock the execute method and its result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_preferences
    mock_db_session.execute.return_value = mock_result

    # 4. Mock the book service call
    with patch('routes.get_books_by_genre', AsyncMock(return_value=mock_books)) as mock_get_books, \
         patch('routes.log_action', AsyncMock()) as mock_log_action:

        # 5. Call the endpoint
        response = client.get(
            "/api/v1/recommendations",
            auth=("testuser", "testpass")
        )

        # 6. Assert response
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["title"] == "Book 1"
        assert response_data[1]["title"] == "Book 2"

        # 7. Assert that mocks were called
        mock_db_session.execute.assert_called_once()
        assert mock_get_books.call_count == 2  # Called once for each genre
        mock_log_action.assert_called_once_with(
            str(mock_user_id),
            "get_recommendations",
            "success",
            f"Retrieved {len(response_data)} unique recommendations"
        )

    # Clean up dependency overrides
    app.dependency_overrides = {}

def test_get_recommendations_no_preferences():
    # 1. Mock dependencies
    mock_db_session = AsyncMock()
    mock_user_id = 123

    # Configure the mock_db_session
    mock_db_session.execute = AsyncMock()

    # 2. Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    # 3. Mock empty preferences
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    # 4. Mock log_action
    with patch('routes.log_action', AsyncMock()) as mock_log_action:

        # 5. Call the endpoint
        response = client.get(
            "/api/v1/recommendations",
            auth=("testuser", "testpass")
        )

        # 6. Assert response
        assert response.status_code == 404
        assert "No preferences found for user" in response.json()["detail"]

        # 7. Assert that mocks were called
        mock_db_session.execute.assert_called_once()
        mock_log_action.assert_called_once_with(
            str(mock_user_id),
            "get_recommendations",
            "error",
            "No preferences found for user"
        )

    # Clean up dependency overrides
    app.dependency_overrides = {} 