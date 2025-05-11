from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from main import app
from routes import get_db, verify_auth

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_generate_review_summary_success():
    # 1. Mock dependencies
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 1

    # Configure the mock_db_session
    mock_db_session.execute = AsyncMock()

    # 2. Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    # 3. Mock the LLaMA3 API response
    mock_llama_response = {"response": "This is a mock summary of the reviews."}

    # 4. Mock httpx.AsyncClient
    with patch(
        "httpx.AsyncClient.post",
        AsyncMock(
            return_value=MagicMock(status_code=200, json=lambda: mock_llama_response)
        ),
    ) as mock_post, patch("routes.log_action", AsyncMock()) as mock_log_action:

        # 5. Prepare request data
        request_data = {
            "book_id": book_id,
            "content": "Sample review content for summarization",
        }

        # 6. Call the endpoint
        response = client.post(
            "/api/v1/generate-review-summary",
            json=request_data,
            auth=("testuser", "testpass"),
        )

        # 7. Assert response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["book_id"] == book_id
        assert response_data["summary"] == mock_llama_response["response"]

        # 8. Assert that mocks were called
        mock_post.assert_called_once()
        mock_log_action.assert_called_once_with(
            user_id=str(mock_user_id),
            action="generate_review_summary",
            status="success",
            details=f"Generated review summary for book {book_id}",
        )

    # Clean up dependency overrides
    app.dependency_overrides = {}


def test_generate_review_summary_llama_error():
    # 1. Mock dependencies
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 1

    # Configure the mock_db_session
    mock_db_session.execute = AsyncMock()

    # 2. Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    # 3. Mock httpx.AsyncClient to simulate LLaMA3 API error
    with patch(
        "httpx.AsyncClient.post", AsyncMock(side_effect=Exception("LLaMA3 API error"))
    ) as mock_post, patch("routes.log_action", AsyncMock()) as mock_log_action:

        # 4. Prepare request data
        request_data = {
            "book_id": book_id,
            "content": "Sample review content for summarization",
        }

        # 5. Call the endpoint
        response = client.post(
            "/api/v1/generate-review-summary",
            json=request_data,
            auth=("testuser", "testpass"),
        )

        # 6. Assert response
        assert response.status_code == 500
        assert "Error generating review summary" in response.json()["detail"]

        # 7. Assert that mocks were called
        mock_post.assert_called_once()
        mock_log_action.assert_called_once_with(
            user_id=str(mock_user_id),
            action="generate_review_summary",
            status="error",
            details="500: Unexpected error during summary generation: LLaMA3 API error",
        )

    # Clean up dependency overrides
    app.dependency_overrides = {}
