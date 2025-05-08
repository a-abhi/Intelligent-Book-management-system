import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from book_service.models import Book
from book_service.schemas import BookCreate

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_create_book_success_with_summary(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    mock_credentials = ("testuser", "testpassword")
    
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "genre": "Fiction",
        "year_published": 2023,
        "summary": "This is a test summary."
    }
    
    expected_book_id = 1
    expected_generated_summary = "Generated summary for Test Book"

    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = None
    mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', expected_book_id)

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.generate_book_summary', AsyncMock(return_value=expected_generated_summary)) as mock_generate_summary, \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.post("/books", json=book_data, auth=mock_credentials)
        
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["id"] == expected_book_id
        assert response_json["title"] == book_data["title"]
        assert response_json["summary"] == expected_generated_summary
        
        mock_generate_summary.assert_called_once_with(
            book_id=expected_book_id,
            content=book_data["summary"],
            auth=mock_credentials
        )
        mock_log_action.assert_called()

@pytest.mark.asyncio
async def test_create_book_success_without_summary_content(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    mock_credentials = ("testuser", "testpassword")
    
    book_data = {
        "title": "Test Book No Summary Content",
        "author": "Test Author",
        "genre": "Sci-Fi",
        "year_published": 2024,
        "summary": ""
    }
    
    expected_book_id = 2

    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = None
    mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', expected_book_id)

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.generate_book_summary', AsyncMock()) as mock_generate_summary, \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.post("/books", json=book_data, auth=mock_credentials)
        
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["id"] == expected_book_id
        assert response_json["title"] == book_data["title"]
        assert response_json["summary"] == ""
        
        mock_generate_summary.assert_not_called()
        mock_log_action.assert_called()

@pytest.mark.asyncio
async def test_create_book_integrity_error(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    mock_credentials = ("testuser", "testpassword")
    
    book_data = {"title": "Existing Book", "author": "Author", "genre": "Genre", "year_published": 2020, "summary": "S"}

    from sqlalchemy.exc import IntegrityError
    mock_db_session.commit.side_effect = IntegrityError("mocked error", params=None, orig=None)
    mock_db_session.rollback.return_value = None

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.post("/books", json=book_data, auth=mock_credentials)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
        mock_db_session.rollback.assert_called_once()
        mock_log_action.assert_called()

@pytest.mark.asyncio
async def test_get_books_success_no_filter(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    
    mock_book_1 = Book(id=1, title="Book 1", author="Author 1", genre="Fiction", year_published=2021, summary="Summary 1")
    mock_book_2 = Book(id=2, title="Book 2", author="Author 2", genre="Sci-Fi", year_published=2022, summary="Summary 2")
    mock_books = [mock_book_1, mock_book_2]

    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = mock_books
    mock_db_session.execute.return_value = mock_result

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.get("/books")
        
        assert response.status_code == 200
        response_json = response.json()
        assert len(response_json) == 2
        assert response_json[0]["title"] == "Book 1"
        assert response_json[1]["title"] == "Book 2"
        mock_log_action.assert_called()

@pytest.mark.asyncio
async def test_get_books_success_with_genre_filter(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    genre_filter = "Fiction"
    
    mock_book_1 = Book(id=1, title="Book 1", author="Author 1", genre="Fiction", year_published=2021, summary="Summary 1")
    mock_filtered_books = [mock_book_1]

    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = mock_filtered_books
    mock_db_session.execute.return_value = mock_result

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.get(f"/books?genre={genre_filter}")
        
        assert response.status_code == 200
        response_json = response.json()
        assert len(response_json) == 1
        assert response_json[0]["title"] == "Book 1"
        assert response_json[0]["genre"] == genre_filter
        mock_log_action.assert_called()

@pytest.mark.asyncio
async def test_get_book_success(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    book_id = 1
    
    mock_book = Book(id=book_id, title="Specific Book", author="Author", genre="Genre", year_published=2020, summary="S")

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_book
    mock_db_session.execute.return_value = mock_result

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.get(f"/books/{book_id}")
        
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["id"] == book_id
        assert response_json["title"] == "Specific Book"
        mock_log_action.assert_called()

@pytest.mark.asyncio
async def test_get_book_not_found(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    book_id = 999

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.get(f"/books/{book_id}")
        
        assert response.status_code == 404
        assert f"Book with ID {book_id} not found" in response.json()["detail"]
        mock_log_action.assert_called()

@pytest.mark.asyncio
async def test_update_book_success_with_summary_generation(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    mock_credentials = ("testuser", "testpassword")
    book_id = 1
    
    update_data = {
        "title": "Updated Title",
        "author": "Updated Author",
        "genre": "Updated Genre",
        "year_published": 2025,
        "summary": "This is an updated summary that needs generation."
    }
    
    mock_existing_book = Book(id=book_id, title="Old Title", author="Old Author", genre="Old Genre", year_published=2020, summary="Old Summary")
    expected_generated_summary = "Generated summary for Updated Title"

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_existing_book
    mock_db_session.execute.return_value = mock_result
    mock_db_session.commit.return_value = None
    async def mock_refresh(obj):
        for key, value in update_data.items():
            if key == "summary":
                setattr(obj, key, expected_generated_summary)
            else:
                setattr(obj, key, value)
    mock_db_session.refresh.side_effect = mock_refresh

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.generate_book_summary', AsyncMock(return_value=expected_generated_summary)) as mock_generate_summary, \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.put(f"/books/{book_id}", json=update_data, auth=mock_credentials)
        
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["id"] == book_id
        assert response_json["title"] == update_data["title"]
        assert response_json["summary"] == expected_generated_summary
        
        mock_generate_summary.assert_called_once_with(
            book_id=book_id,
            content=update_data["summary"],
            auth=mock_credentials
        )
        mock_log_action.assert_called()
        mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_book_success_without_summary_update(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    mock_credentials = ("testuser", "testpassword")
    book_id = 2
    
    update_data = {
        "title": "Another Updated Title",
        "year_published": 2022
    }
    
    mock_existing_book = Book(id=book_id, title="Original Title", author="Author", genre="Genre", year_published=2021, summary="Existing Summary")

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_existing_book
    mock_db_session.execute.return_value = mock_result
    mock_db_session.commit.return_value = None
    async def mock_refresh(obj):
        for key, value in update_data.items():
            setattr(obj, key, value)
        setattr(obj, 'summary', mock_existing_book.summary)
    mock_db_session.refresh.side_effect = mock_refresh

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.generate_book_summary', AsyncMock()) as mock_generate_summary, \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.put(f"/books/{book_id}", json=update_data, auth=mock_credentials)
        
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["id"] == book_id
        assert response_json["title"] == update_data["title"]
        assert response_json["summary"] == mock_existing_book.summary
        
        mock_generate_summary.assert_not_called()
        mock_log_action.assert_called()
        mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_book_not_found(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    mock_credentials = ("testuser", "testpassword")
    book_id = 999
    update_data = {"title": "Won't Matter"}

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.put(f"/books/{book_id}", json=update_data, auth=mock_credentials)
        
        assert response.status_code == 404
        assert f"Book with ID {book_id} not found" in response.json()["detail"]
        mock_log_action.assert_called()
        mock_db_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_delete_book_success(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    book_id = 1
    
    mock_book_to_delete = Book(id=book_id, title="Book to Delete", author="Author", genre="Genre", year_published=2020, summary="S")

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_book_to_delete
    mock_db_session.execute.return_value = mock_result
    mock_db_session.delete.return_value = None
    mock_db_session.commit.return_value = None

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.delete(f"/books/{book_id}")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Book deleted successfully"}
        mock_db_session.delete.assert_called_once_with(mock_book_to_delete)
        mock_db_session.commit.assert_called_once()
        mock_log_action.assert_called()

@pytest.mark.asyncio
async def test_delete_book_not_found(async_client: AsyncClient):
    mock_db_session = AsyncMock()
    mock_user_id = 1
    book_id = 999

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    with patch('book_service.routes.get_db', return_value=mock_db_session), \
         patch('book_service.routes.verify_auth', return_value=mock_user_id), \
         patch('book_service.routes.log_action', AsyncMock()) as mock_log_action:
        
        response = await async_client.delete(f"/books/{book_id}")
        
        assert response.status_code == 404
        assert f"Book with ID {book_id} not found" in response.json()["detail"]
        mock_log_action.assert_called()
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()

