import pytest
from fastapi.testclient import TestClient
from models import Book
import json

def test_create_book_success(
    client: TestClient,
    mock_auth,
    test_credentials,
    sample_book_data
):
    """Test successful book creation endpoint."""
    response = client.post(
        "/api/v1/books",
        json=sample_book_data,
        auth=test_credentials
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == sample_book_data["title"]
    assert data["author"] == sample_book_data["author"]
    assert data["genre"] == sample_book_data["genre"]
    assert data["year_published"] == sample_book_data["year_published"]
    assert data["summary"] == sample_book_data["summary"]

def test_create_book_unauthorized(
    client: TestClient,
    sample_book_data
):
    """Test book creation without authentication."""
    response = client.post(
        "/api/v1/books",
        json=sample_book_data
    )
    
    assert response.status_code == 401

def test_get_book_success(
    client: TestClient,
    mock_auth,
    test_credentials,
    test_db,
    sample_book_data
):
    """Test getting a book by ID."""
    # Create a test book
    async def create_test_book():
        engine, async_session, init_test_db = test_db
        await init_test_db()
        async with async_session() as session:
            book = Book(**sample_book_data)
            session.add(book)
            await session.commit()
            return book.id
    
    import asyncio
    book_id = asyncio.run(create_test_book())
    
    response = client.get(
        f"/api/v1/books/{book_id}",
        auth=test_credentials
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book_id
    assert data["title"] == sample_book_data["title"]
    assert data["author"] == sample_book_data["author"]
    assert data["genre"] == sample_book_data["genre"]
    assert data["year_published"] == sample_book_data["year_published"]
    assert data["summary"] == sample_book_data["summary"]

def test_get_book_not_found(
    client: TestClient,
    mock_auth,
    test_credentials
):
    """Test getting a non-existent book."""
    response = client.get(
        "/api/v1/books/999",
        auth=test_credentials
    )
    
    assert response.status_code == 404
    assert "Book not found" in response.json()["detail"]

def test_update_book_success(
    client: TestClient,
    mock_auth,
    test_credentials,
    test_db,
    sample_book_data
):
    """Test successful book update."""
    # Create a test book
    async def create_test_book():
        engine, async_session, init_test_db = test_db
        await init_test_db()
        async with async_session() as session:
            book = Book(**sample_book_data)
            session.add(book)
            await session.commit()
            return book.id
    
    import asyncio
    book_id = asyncio.run(create_test_book())
    
    update_data = {
        "title": "Updated Title",
        "author": "Updated Author",
        "genre": "Updated Genre",
        "year_published": 2025,
        "summary": "Updated summary"
    }
    
    response = client.put(
        f"/api/v1/books/{book_id}",
        json=update_data,
        auth=test_credentials
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book_id
    assert data["title"] == update_data["title"]
    assert data["author"] == update_data["author"]
    assert data["genre"] == update_data["genre"]
    assert data["year_published"] == update_data["year_published"]
    assert data["summary"] == update_data["summary"]

def test_delete_book_success(
    client: TestClient,
    mock_auth,
    test_credentials,
    test_db,
    sample_book_data
):
    """Test successful book deletion."""
    # Create a test book
    async def create_test_book():
        engine, async_session, init_test_db = test_db
        await init_test_db()
        async with async_session() as session:
            book = Book(**sample_book_data)
            session.add(book)
            await session.commit()
            return book.id
    
    import asyncio
    book_id = asyncio.run(create_test_book())
    
    response = client.delete(
        f"/api/v1/books/{book_id}",
        auth=test_credentials
    )
    
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(
        f"/api/v1/books/{book_id}",
        auth=test_credentials
    )
    assert get_response.status_code == 404

def test_search_books_success(
    client: TestClient,
    mock_auth,
    test_credentials,
    test_db,
    sample_book_data
):
    """Test successful book search."""
    # Create test books
    async def create_test_books():
        engine, async_session, init_test_db = test_db
        await init_test_db()
        async with async_session() as session:
            books = [
                Book(**sample_book_data),
                Book(**{**sample_book_data, "title": "Another Book"})
            ]
            for book in books:
                session.add(book)
            await session.commit()
    
    import asyncio
    asyncio.run(create_test_books())
    
    response = client.get(
        "/api/v1/books/search?query=Test",
        auth=test_credentials
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == sample_book_data["title"] 