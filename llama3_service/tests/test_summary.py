import pytest
from fastapi.testclient import TestClient
from ..main import app
from ..summary_utils import get_cached_summary

client = TestClient(app)

@pytest.fixture
def test_user():
    return {
        "username": "testuser",
        "password": "testpass"
    }

@pytest.fixture
def test_content():
    return "This is a test content that needs to be summarized. " * 10

def test_generate_summary(test_user, test_content):
    # First register and login
    client.post("/auth/register", json=test_user)
    login_response = client.post("/auth/login", auth=(test_user["username"], test_user["password"]))
    
    # Generate summary
    response = client.post(
        "/generate-summary",
        json={"content": test_content},
        auth=(test_user["username"], test_user["password"])
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert len(data["summary"]) > 0

def test_generate_summary_unauthorized(test_content):
    response = client.post(
        "/generate-summary",
        json={"content": test_content}
    )
    assert response.status_code == 401

def test_generate_summary_invalid_content(test_user):
    # First register and login
    client.post("/auth/register", json=test_user)
    
    # Generate summary with empty content
    response = client.post(
        "/generate-summary",
        json={"content": ""},
        auth=(test_user["username"], test_user["password"])
    )
    assert response.status_code == 422

def test_summary_caching(test_content):
    # Test that the same content returns the same summary
    summary1 = get_cached_summary(test_content)
    summary2 = get_cached_summary(test_content)
    assert summary1 == summary2

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"} 