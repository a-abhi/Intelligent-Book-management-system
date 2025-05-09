import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock, MagicMock
import uuid
from main import app
from schemas import ReviewCreate, ReviewResponse
from models import Review
from routes import get_db, verify_auth

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_review_success(client):
    mock_db_session = AsyncMock()
    mock_user_id = 123
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id
    book_id = 1
    review_data = {"rating": 5, "comment": "Great book!"}

    response = client.post(
        f"/api/v1/books/{book_id}/reviews",
        json=review_data,
        auth=("testuser", "testpass") # Basic auth
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["book_id"] == book_id
    assert json_response["rating"] == review_data["rating"]
    assert json_response["comment"] == review_data["comment"]
    assert "id" in json_response
    assert "user_id" in json_response # This will be the UUID from mock_verify_auth
    
    app.dependency_overrides = {}


def test_get_reviews_success(
    client, mock_db_session, mock_verify_auth, mock_verify_book_exists, mock_log_action
):
    app.dependency_overrides[db.get_db] = lambda: mock_db_session

    book_id = 1
    user_id = mock_verify_auth.return_value
    
    mock_reviews = [
        Review(id=1, book_id=book_id, user_id=uuid.uuid4(), rating=5, comment="Excellent!"),
        Review(id=2, book_id=book_id, user_id=uuid.uuid4(), rating=4, comment="Good read.")
    ]
    
    # Mock the execute method and its result
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = mock_reviews
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    response = client.get(
        f"/api/v1/books/{book_id}/reviews",
        auth=("testuser", "testpass")
    )

    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2
    assert json_response[0]["comment"] == "Excellent!"
    assert json_response[1]["rating"] == 4
    
    mock_verify_book_exists.assert_called_once_with(str(book_id), ("testuser", "testpass"))
    mock_db_session.execute.assert_called_once()
    mock_log_action.assert_called_with(str(user_id), "get_reviews", "success", f"Retrieved reviews for book {book_id}")

    del app.dependency_overrides[db.get_db]

def test_create_review_book_not_found(
    client, mock_db_session, mock_verify_auth, mock_verify_book_exists, mock_log_action
):
    app.dependency_overrides[db.get_db] = lambda: mock_db_session
    
    book_id = 999 # Non-existent book
    review_data = {"rating": 5, "comment": "Great book!"}
    user_id = mock_verify_auth.return_value

    # Mock verify_book_exists to raise HTTPException for not found
    from fastapi import HTTPException, status
    mock_verify_book_exists.side_effect = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    response = client.post(
        f"/api/v1/books/{book_id}/reviews",
        json=review_data,
        auth=("testuser", "testpass")
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"
    
    mock_verify_book_exists.assert_called_once_with(str(book_id), ("testuser", "testpass"))
    mock_log_action.assert_not_called() # Should not be called if book verification fails early

    del app.dependency_overrides[db.get_db]

def test_get_book_reviews_summary_success(
    client,
    mock_db_session,
    mock_verify_auth,
    mock_verify_book_exists,
    mock_generate_book_reviews_summary,
    mock_log_action
):
    app.dependency_overrides[db.get_db] = lambda: mock_db_session

    book_id = 1
    user_id = mock_verify_auth.return_value
    mock_summary_text = "This is a great book with many positive reviews."
    
    mock_reviews_data = [
        Review(id=1, book_id=book_id, user_id=uuid.uuid4(), rating=5, comment="Excellent!"),
        Review(id=2, book_id=book_id, user_id=uuid.uuid4(), rating=4, comment="Good read."),
        Review(id=3, book_id=book_id, user_id=uuid.uuid4(), rating=4.5, comment="Very insightful.")
    ]
    
    # Mock DB execution for fetching reviews
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = mock_reviews_data
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    # Mock the summary generation
    mock_generate_book_reviews_summary.return_value = mock_summary_text

    response = client.get(
        f"/api/v1/books/{book_id}/reviews/summary",
        auth=("testuser", "testpass")
    )

    assert response.status_code == 200
    json_response = response.json()
    
    assert json_response["book_id"] == book_id
    assert json_response["summary"] == mock_summary_text
    assert json_response["total_reviews"] == len(mock_reviews_data)
    
    expected_avg_rating = sum(r.rating for r in mock_reviews_data) / len(mock_reviews_data)
    assert abs(json_response["average_rating"] - expected_avg_rating) < 0.0001 # Compare floats with tolerance

    mock_verify_book_exists.assert_called_once_with(str(book_id), ("testuser", "testpass"))
    mock_db_session.execute.assert_called_once()
    mock_generate_book_reviews_summary.assert_called_once_with(
        reviews=mock_reviews_data,
        auth=("testuser", "testpass")
    )
    mock_log_action.assert_called_with(
        user_id=str(user_id),
        action="get_book_reviews_summary",
        status="success",
        details=f"Generated summary for book {book_id}"
    )

    del app.dependency_overrides[db.get_db]
