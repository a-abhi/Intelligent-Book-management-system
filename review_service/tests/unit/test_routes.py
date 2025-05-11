import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from main import app
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
    # 1. Mock dependencies
    mock_db_session = AsyncMock()
    mock_user_id = 123  # Changed from UUID to integer
    book_id = 1

    # Configure the mock_db_session
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    # 2. Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    # 3. Mock verify_book_exists
    with patch("routes.verify_book_exists", AsyncMock()) as mock_verify_book:
        # 4. Prepare request data
        review_data = {"rating": 4.5, "comment": "Great book with excellent content!"}

        # Configure mock_db_session.refresh
        async def refresh_side_effect(review_instance):
            if isinstance(review_instance, Review):
                review_instance.id = 1
                review_instance.book_id = book_id  # Set the book_id
                review_instance.user_id = mock_user_id  # Set the user_id
                current_time = datetime.utcnow()
                review_instance.created_at = current_time
                review_instance.updated_at = current_time
            return None

        mock_db_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        # 5. Call the endpoint
        response = client.post(
            f"/api/v1/books/{book_id}/reviews",
            json=review_data,
            auth=("testuser", "testpass"),
        )

        # 6. Assert response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["rating"] == review_data["rating"]
        assert response_data["comment"] == review_data["comment"]
        assert response_data["book_id"] == book_id
        assert response_data["user_id"] == mock_user_id
        assert "id" in response_data
        assert "created_at" in response_data
        assert "updated_at" in response_data

        # 7. Assert that mocks were called
        mock_verify_book.assert_called_once_with(str(book_id), ("testuser", "testpass"))
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    # Clean up dependency overrides
    app.dependency_overrides = {}


def test_create_review_invalid_rating(client):
    mock_db_session = AsyncMock()
    mock_user_id = uuid.uuid4()
    book_id = 1

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch("routes.verify_book_exists", AsyncMock()):
        # Test with invalid rating
        review_data = {"rating": 6.0, "comment": "Great book!"}  # Invalid rating > 5.0

        response = client.post(
            f"/api/v1/books/{book_id}/reviews",
            json=review_data,
            auth=("testuser", "testpass"),
        )

        assert response.status_code == 422  # Validation error
        assert "rating" in response.json()["detail"][0]["loc"]

    app.dependency_overrides = {}


def test_get_reviews_success(client):
    # 1. Mock dependencies
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 1

    # Configure the mock_db_session
    mock_db_session.execute = AsyncMock()

    # 2. Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    # 3. Mock verify_book_exists and log_action
    with patch("routes.verify_book_exists", AsyncMock()) as mock_verify_book, patch(
        "routes.log_action", AsyncMock()
    ) as mock_log_action:

        # Create mock reviews
        mock_reviews = [
            Review(
                id=1,
                book_id=book_id,
                user_id=mock_user_id,
                rating=5.0,
                comment="Excellent!",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            Review(
                id=2,
                book_id=book_id,
                user_id=mock_user_id,
                rating=4.0,
                comment="Good read.",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]

        # Mock the execute method and its result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute.return_value = mock_result

        # 4. Call the endpoint
        response = client.get(
            f"/api/v1/books/{book_id}/reviews", auth=("testuser", "testpass")
        )

        # 5. Assert response
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["comment"] == "Excellent!"
        assert response_data[1]["rating"] == 4.0

        # 6. Assert that mocks were called
        mock_verify_book.assert_called_once_with(str(book_id), ("testuser", "testpass"))
        mock_db_session.execute.assert_called_once()
        mock_log_action.assert_called_once_with(
            str(mock_user_id),
            "get_reviews",
            "success",
            f"Retrieved reviews for book {book_id}",
        )

    # Clean up dependency overrides
    app.dependency_overrides = {}


def test_create_review_book_not_found(client):
    # 1. Mock dependencies
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 999  # Non-existent book

    # Configure the mock_db_session
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    # 2. Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    # 3. Mock verify_book_exists to raise HTTPException
    with patch(
        "routes.verify_book_exists",
        AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
            )
        ),
    ) as mock_verify_book, patch("routes.log_action", AsyncMock()) as mock_log_action:

        # 4. Prepare request data
        review_data = {"rating": 5.0, "comment": "Great book!"}

        # 5. Call the endpoint
        response = client.post(
            f"/api/v1/books/{book_id}/reviews",
            json=review_data,
            auth=("testuser", "testpass"),
        )

        # 6. Assert response
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"

        # 7. Assert that mocks were called
        mock_verify_book.assert_called_once_with(str(book_id), ("testuser", "testpass"))
        mock_db_session.add.assert_not_called()  # Should not be called if book verification fails
        mock_db_session.commit.assert_not_called()  # Should not be called if book verification fails
        mock_log_action.assert_not_called()  # Should not be called if book verification fails

    # Clean up dependency overrides
    app.dependency_overrides = {}


def test_get_book_reviews_summary_success(client):
    # 1. Mock dependencies
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 1

    # Configure the mock_db_session
    mock_db_session.execute = AsyncMock()

    # 2. Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    # 3. Mock verify_book_exists and generate_book_reviews_summary
    with patch("routes.verify_book_exists", AsyncMock()) as mock_verify_book, patch(
        "routes.generate_book_reviews_summary",
        AsyncMock(return_value="This is a mock summary of the reviews."),
    ) as mock_generate_summary, patch(
        "routes.log_action", AsyncMock()
    ) as mock_log_action:

        # Create mock reviews
        mock_reviews = [
            Review(
                id=1,
                book_id=book_id,
                user_id=mock_user_id,
                rating=4.5,
                comment="Great book!",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            Review(
                id=2,
                book_id=book_id,
                user_id=mock_user_id,
                rating=5.0,
                comment="Excellent!",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]

        # Mock the execute method and its result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute.return_value = mock_result

        response = client.get(
            f"/api/v1/books/{book_id}/reviews/summary", auth=("testuser", "testpass")
        )

        # 5. Assert response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["book_id"] == book_id
        assert response_data["summary"] == "This is a mock summary of the reviews."
        assert response_data["total_reviews"] == len(mock_reviews)

        expected_avg_rating = sum(r.rating for r in mock_reviews) / len(mock_reviews)
        assert (
            abs(response_data["average_rating"] - expected_avg_rating) < 0.0001
        )  # Compare floats with tolerance

        # 6. Assert that mocks were called
        mock_verify_book.assert_called_once_with(str(book_id), ("testuser", "testpass"))
        mock_db_session.execute.assert_called_once()
        mock_generate_summary.assert_called_once_with(
            reviews=mock_reviews, auth=("testuser", "testpass")
        )
        mock_log_action.assert_called_once_with(
            user_id=str(mock_user_id),
            action="get_book_reviews_summary",
            status="success",
            details=f"Generated summary for book {book_id}",
        )

    # Clean up dependency overrides
    app.dependency_overrides = {}


def test_get_book_reviews_summary_no_reviews(client):
    mock_db_session = AsyncMock()
    mock_user_id = uuid.uuid4()
    book_id = 1

    # Mock empty result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch("routes.verify_book_exists", AsyncMock()) as mock_verify_book:
        response = client.get(
            f"/api/v1/books/{book_id}/reviews/summary", auth=("testuser", "testpass")
        )

        assert response.status_code == 404
        assert (
            f"No reviews found for book with ID {book_id}" in response.json()["detail"]
        )

        mock_verify_book.assert_called_once_with(str(book_id), ("testuser", "testpass"))
        mock_db_session.execute.assert_called_once()

    app.dependency_overrides = {}


def test_get_book_reviews_summary_llama3_service_error(client):
    mock_db_session = AsyncMock()
    mock_user_id = uuid.uuid4()
    book_id = 1

    # Create mock reviews
    mock_reviews = [
        Review(
            id=1,
            book_id=book_id,
            user_id=mock_user_id,
            rating=4.5,
            comment="Great book!",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    ]

    # Mock the execute method and its result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_reviews
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    # Mock the summary generation to raise an error
    mock_generate_summary = AsyncMock(side_effect=Exception("LLaMA3 service error"))

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch("routes.verify_book_exists", AsyncMock()) as mock_verify_book, patch(
        "routes.generate_book_reviews_summary", mock_generate_summary
    ):

        response = client.get(
            f"/api/v1/books/{book_id}/reviews/summary", auth=("testuser", "testpass")
        )

        assert response.status_code == 500
        assert (
            "An error occurred while generating the summary"
            in response.json()["detail"]
        )

        mock_verify_book.assert_called_once_with(str(book_id), ("testuser", "testpass"))
        mock_db_session.execute.assert_called_once()
        mock_generate_summary.assert_called_once()

    app.dependency_overrides = {}
