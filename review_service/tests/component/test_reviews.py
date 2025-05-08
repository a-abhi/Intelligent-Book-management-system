import pytest
from fastapi import status
from unittest.mock import patch

@pytest.mark.asyncio
async def test_create_review_success(client, mock_auth, mock_book_service, sample_review_data):
    """Test successful review creation."""
    with patch('utils.book.verify_book_exists', return_value=True):
        response = client.post(
            "/api/v1/reviews",
            json=sample_review_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["book_id"] == sample_review_data["book_id"]
        assert data["rating"] == sample_review_data["rating"]
        assert data["comment"] == sample_review_data["comment"]
        assert data["user_id"] == sample_review_data["user_id"]

@pytest.mark.asyncio
async def test_create_review_unauthorized(client, sample_review_data):
    """Test review creation without authentication."""
    response = client.post(
        "/api/v1/reviews",
        json=sample_review_data
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_create_review_book_not_found(client, mock_auth, sample_review_data):
    """Test review creation for non-existent book."""
    with patch('utils.book.verify_book_exists', return_value=False):
        response = client.post(
            "/api/v1/reviews",
            json=sample_review_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_review_by_id_success(client, mock_auth, sample_review_data):
    """Test getting a review by ID."""
    # First create a review
    with patch('utils.book.verify_book_exists', return_value=True):
        create_response = client.post(
            "/api/v1/reviews",
            json=sample_review_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        review_id = create_response.json()["id"]
        
        # Then get the review
        response = client.get(
            f"/api/v1/reviews/{review_id}",
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == review_id
        assert data["book_id"] == sample_review_data["book_id"]
        assert data["rating"] == sample_review_data["rating"]

@pytest.mark.asyncio
async def test_get_review_not_found(client, mock_auth):
    """Test getting a non-existent review."""
    response = client.get(
        "/api/v1/reviews/999",
        headers={"Authorization": f"Basic {mock_auth}"}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_review_success(client, mock_auth, sample_review_data):
    """Test successful review update."""
    # First create a review
    with patch('utils.book.verify_book_exists', return_value=True):
        create_response = client.post(
            "/api/v1/reviews",
            json=sample_review_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        review_id = create_response.json()["id"]
        
        # Then update the review
        update_data = {"rating": 5, "comment": "Updated review comment"}
        response = client.put(
            f"/api/v1/reviews/{review_id}",
            json=update_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == review_id
        assert data["rating"] == 5
        assert data["comment"] == "Updated review comment"
        assert data["book_id"] == sample_review_data["book_id"]  # Unchanged field

@pytest.mark.asyncio
async def test_delete_review_success(client, mock_auth, sample_review_data):
    """Test successful review deletion."""
    # First create a review
    with patch('utils.book.verify_book_exists', return_value=True):
        create_response = client.post(
            "/api/v1/reviews",
            json=sample_review_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        review_id = create_response.json()["id"]
        
        # Then delete the review
        response = client.delete(
            f"/api/v1/reviews/{review_id}",
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        get_response = client.get(
            f"/api/v1/reviews/{review_id}",
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_book_reviews_success(client, mock_auth, sample_review_data):
    """Test getting all reviews for a book."""
    # Create multiple reviews for the same book
    with patch('utils.book.verify_book_exists', return_value=True):
        for i in range(2):
            review_data = {
                **sample_review_data,
                "rating": i + 1,
                "comment": f"Review {i + 1}"
            }
            client.post(
                "/api/v1/reviews",
                json=review_data,
                headers={"Authorization": f"Basic {mock_auth}"}
            )
        
        # Get all reviews for the book
        response = client.get(
            f"/api/v1/books/{sample_review_data['book_id']}/reviews",
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert all(review["book_id"] == sample_review_data["book_id"] for review in data) 