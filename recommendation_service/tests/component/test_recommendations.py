import pytest
from fastapi import status
from unittest.mock import patch

@pytest.mark.asyncio
async def test_create_recommendation_success(client, mock_auth, mock_book_service, mock_review_service, sample_recommendation_data):
    """Test successful recommendation creation."""
    with patch('utils.book.verify_book_exists', return_value=True):
        response = client.post(
            "/api/v1/recommendations",
            json=sample_recommendation_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["book_id"] == sample_recommendation_data["book_id"]
        assert data["user_id"] == sample_recommendation_data["user_id"]
        assert data["score"] == sample_recommendation_data["score"]
        assert data["reason"] == sample_recommendation_data["reason"]

@pytest.mark.asyncio
async def test_create_recommendation_unauthorized(client, sample_recommendation_data):
    """Test recommendation creation without authentication."""
    response = client.post(
        "/api/v1/recommendations",
        json=sample_recommendation_data
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_create_recommendation_book_not_found(client, mock_auth, sample_recommendation_data):
    """Test recommendation creation for non-existent book."""
    with patch('utils.book.verify_book_exists', return_value=False):
        response = client.post(
            "/api/v1/recommendations",
            json=sample_recommendation_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_recommendation_by_id_success(client, mock_auth, sample_recommendation_data):
    """Test getting a recommendation by ID."""
    # First create a recommendation
    with patch('utils.book.verify_book_exists', return_value=True):
        create_response = client.post(
            "/api/v1/recommendations",
            json=sample_recommendation_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        recommendation_id = create_response.json()["id"]
        
        # Then get the recommendation
        response = client.get(
            f"/api/v1/recommendations/{recommendation_id}",
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == recommendation_id
        assert data["book_id"] == sample_recommendation_data["book_id"]
        assert data["score"] == sample_recommendation_data["score"]

@pytest.mark.asyncio
async def test_get_recommendation_not_found(client, mock_auth):
    """Test getting a non-existent recommendation."""
    response = client.get(
        "/api/v1/recommendations/999",
        headers={"Authorization": f"Basic {mock_auth}"}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_recommendation_success(client, mock_auth, sample_recommendation_data):
    """Test successful recommendation update."""
    # First create a recommendation
    with patch('utils.book.verify_book_exists', return_value=True):
        create_response = client.post(
            "/api/v1/recommendations",
            json=sample_recommendation_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        recommendation_id = create_response.json()["id"]
        
        # Then update the recommendation
        update_data = {"score": 0.95, "reason": "Updated recommendation reason"}
        response = client.put(
            f"/api/v1/recommendations/{recommendation_id}",
            json=update_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == recommendation_id
        assert data["score"] == 0.95
        assert data["reason"] == "Updated recommendation reason"
        assert data["book_id"] == sample_recommendation_data["book_id"]  # Unchanged field

@pytest.mark.asyncio
async def test_delete_recommendation_success(client, mock_auth, sample_recommendation_data):
    """Test successful recommendation deletion."""
    # First create a recommendation
    with patch('utils.book.verify_book_exists', return_value=True):
        create_response = client.post(
            "/api/v1/recommendations",
            json=sample_recommendation_data,
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        recommendation_id = create_response.json()["id"]
        
        # Then delete the recommendation
        response = client.delete(
            f"/api/v1/recommendations/{recommendation_id}",
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        get_response = client.get(
            f"/api/v1/recommendations/{recommendation_id}",
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_user_recommendations_success(client, mock_auth, sample_recommendation_data):
    """Test getting all recommendations for a user."""
    # Create multiple recommendations for the same user
    with patch('utils.book.verify_book_exists', return_value=True):
        for i in range(2):
            recommendation_data = {
                **sample_recommendation_data,
                "book_id": i + 1,
                "score": 0.8 + (i * 0.1)
            }
            client.post(
                "/api/v1/recommendations",
                json=recommendation_data,
                headers={"Authorization": f"Basic {mock_auth}"}
            )
        
        # Get all recommendations for the user
        response = client.get(
            f"/api/v1/users/{sample_recommendation_data['user_id']}/recommendations",
            headers={"Authorization": f"Basic {mock_auth}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert all(rec["user_id"] == sample_recommendation_data["user_id"] for rec in data) 