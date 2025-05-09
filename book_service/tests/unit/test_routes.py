from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime # Added import

from main import app # Assuming your FastAPI app instance is named 'app' in main.py
from routes import get_db, verify_auth # Import dependencies to mock
from utils.book import generate_book_summary # Import dependency to mock
from schemas import BookCreate, BookResponse
from models import Book

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health") # Note the /api/v1 prefix from your main.py
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_book_success_with_summary_mocked():
    # 1. Mock dependencies
    mock_db_session = AsyncMock()
    mock_user_id = 123
    mock_generated_summary = "This is a mock summary."

    # Configure the mock_db_session if its methods are called
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    # Mock generate_book_summary
    mock_summary_gen = AsyncMock(return_value=mock_generated_summary)

    # 2. Override dependencies in the app for this test
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id
    # We need to patch the generate_book_summary where it's imported in routes.py
    with patch('routes.generate_book_summary', mock_summary_gen):
        # 3. Prepare request data
        book_data = {
            "title": "Test Book with Summary",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2024,
            "summary": "Original content for summary" # This will be used by generate_book_summary
        }
        expected_book_id = 1 # Assuming the DB would assign an ID

        # Configure mock_db_session.refresh to populate the id (and other fields)
        # This simulates the book object being refreshed after commit
        async def refresh_side_effect(book_instance):
            if isinstance(book_instance, Book):
                book_instance.id = expected_book_id
                current_time = datetime.utcnow()
                # Set created_at if not already set (simulates DB default on creation)
                if not getattr(book_instance, 'created_at', None):
                    book_instance.created_at = current_time
                # Always set updated_at (simulates DB onupdate or default)
                book_instance.updated_at = current_time
            return None
        mock_db_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        # 4. Call the endpoint
        response = client.post(
            "/api/v1/books",
            json=book_data,
            auth=("testuser", "testpass") # Basic auth, verify_auth is mocked anyway
        )

        # 5. Assert response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["title"] == book_data["title"]
        assert response_data["author"] == book_data["author"]
        assert response_data["summary"] == mock_generated_summary # Check if mocked summary is used
        assert response_data["id"] == expected_book_id
        assert "created_at" in response_data and response_data["created_at"] is not None
        assert "updated_at" in response_data and response_data["updated_at"] is not None

        # 6. Assert that mocks were called
        mock_db_session.add.assert_called_once()
        # commit is called twice: once after adding the book, once after updating the summary
        assert mock_db_session.commit.call_count == 2
        # refresh is called twice for the same reasons
        assert mock_db_session.refresh.call_count == 2

        # Assert generate_book_summary was called correctly
        mock_summary_gen.assert_awaited_once_with(
            book_id=expected_book_id,
            content=book_data["summary"],
            auth=("testuser", "testpass")
        )

    # Clean up dependency overrides
    app.dependency_overrides = {}

def test_create_book_success_no_initial_summary_mocked():
    # Test case where book.summary is initially None or empty, so generate_book_summary is not called
    mock_db_session = AsyncMock()
    mock_user_id = 123

    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    # Patch generate_book_summary to ensure it's NOT called
    with patch('routes.generate_book_summary', AsyncMock()) as mock_summary_gen_not_called:
        book_data = {
            "title": "Test Book No Summary",
            "author": "Test Author",
            "genre": "Non-Fiction",
            "year_published": 2023,
            "summary": None # No initial summary
        }
        expected_book_id = 2

        async def refresh_side_effect(book_instance):
            if isinstance(book_instance, Book):
                book_instance.id = expected_book_id
                current_time = datetime.utcnow()
                if not getattr(book_instance, 'created_at', None):
                    book_instance.created_at = current_time
                book_instance.updated_at = current_time
            return None
        mock_db_session.refresh = AsyncMock(side_effect=refresh_side_effect)

        response = client.post(
            "/api/v1/books",
            json=book_data,
            auth=("testuser", "testpass")
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["title"] == book_data["title"]
        assert response_data["summary"] is None # Summary should remain None
        assert response_data["id"] == expected_book_id
        assert "created_at" in response_data and response_data["created_at"] is not None
        assert "updated_at" in response_data and response_data["updated_at"] is not None

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once() # Only called once as no summary update
        mock_db_session.refresh.assert_called_once()

        mock_summary_gen_not_called.assert_not_called() # Crucial check

    app.dependency_overrides = {}

# Tests for GET /books
def test_get_books_success():
    mock_db_session = AsyncMock()
    mock_user_id = 123

    # Sample book data to be returned by the mock
    mock_book_1 = Book(id=1, title="Book 1", author="Author 1", genre="Fiction", year_published=2020, summary="Summary 1", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    mock_book_2 = Book(id=2, title="Book 2", author="Author 2", genre="Science", year_published=2021, summary="Summary 2", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    mock_books = [mock_book_1, mock_book_2]

    # Mock the execute method and its result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_books
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch('routes.log_action', AsyncMock()) as mock_log_action:
        response = client.get("/api/v1/books", auth=("testuser", "testpass"))

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["title"] == "Book 1"
        assert response_data[1]["title"] == "Book 2"

        mock_db_session.execute.assert_called_once()
        mock_log_action.assert_awaited_once()

    app.dependency_overrides = {}

def test_get_books_empty_success():
    mock_db_session = AsyncMock()
    mock_user_id = 123

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [] # No books
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch('routes.log_action', AsyncMock()) as mock_log_action:
        response = client.get("/api/v1/books", auth=("testuser", "testpass"))

        assert response.status_code == 200
        assert response.json() == []
        mock_log_action.assert_awaited_once()

    app.dependency_overrides = {}

def test_get_books_db_error():
    mock_db_session = AsyncMock()
    mock_user_id = 123

    mock_db_session.execute = AsyncMock(side_effect=Exception("DB error"))

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch('routes.log_action', AsyncMock()) as mock_log_action:
        response = client.get("/api/v1/books", auth=("testuser", "testpass"))

        assert response.status_code == 500
        assert "Error fetching books" in response.json()["detail"]
        mock_log_action.assert_awaited_once() # Log action should still be called for failure

    app.dependency_overrides = {}

# Tests for GET /books/{book_id}
def test_get_book_by_id_success():
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 1
    mock_book = Book(id=book_id, title="Specific Book", author="Author S", genre="Mystery", year_published=2022, summary="Summary S", created_at=datetime.utcnow(), updated_at=datetime.utcnow())

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_book
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch('routes.log_action', AsyncMock()) as mock_log_action:
        response = client.get(f"/api/v1/books/{book_id}", auth=("testuser", "testpass"))

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["title"] == "Specific Book"
        assert response_data["id"] == book_id
        mock_log_action.assert_awaited_once()

    app.dependency_overrides = {}

def test_get_book_by_id_not_found():
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 999 # Non-existent ID

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None # Book not found
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch('routes.log_action', AsyncMock()) as mock_log_action:
        response = client.get(f"/api/v1/books/{book_id}", auth=("testuser", "testpass"))

        assert response.status_code == 404
        assert f"Book with ID {book_id} not found" in response.json()["detail"]
        mock_log_action.assert_awaited_once()

    app.dependency_overrides = {}

def test_get_book_by_id_db_error():
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 1

    mock_db_session.execute = AsyncMock(side_effect=Exception("DB error"))

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch('routes.log_action', AsyncMock()) as mock_log_action:
        response = client.get(f"/api/v1/books/{book_id}", auth=("testuser", "testpass"))

        assert response.status_code == 500
        assert "Error fetching book" in response.json()["detail"]
        mock_log_action.assert_awaited_once()

    app.dependency_overrides = {}

# Tests for PUT /books/{book_id}
def test_update_book_success():
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 1

    original_book = Book(id=book_id, title="Original Title", author="Original Author", genre="Fiction", year_published=2020, summary="Original Summary", created_at=datetime.utcnow(), updated_at=datetime.utcnow())

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = original_book
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()

    async def refresh_side_effect(book_instance):
        # Simulate that updated_at is changed
        book_instance.updated_at = datetime.utcnow()
        return None
    mock_db_session.refresh = AsyncMock(side_effect=refresh_side_effect)

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    update_data = {"title": "Updated Title", "summary": "Updated Summary"}

    # Patch generate_book_summary as it might be called
    with patch('routes.generate_book_summary', AsyncMock(return_value=update_data["summary"])) as mock_gen_summary, \
         patch('routes.log_action', AsyncMock()) as mock_log_action:

        response = client.put(f"/api/v1/books/{book_id}", json=update_data, auth=("testuser", "testpass"))

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["title"] == "Updated Title"
        assert response_data["summary"] == "Updated Summary" # Assuming generate_book_summary returns the same if called
        assert response_data["id"] == book_id

        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        mock_gen_summary.assert_awaited_once() # generate_book_summary should be called
        mock_log_action.assert_awaited_once()

    app.dependency_overrides = {}

def test_update_book_success_no_summary_change():
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 1

    original_book = Book(id=book_id, title="Original Title", author="Original Author", genre="Fiction", year_published=2020, summary="Original Summary", created_at=datetime.utcnow(), updated_at=datetime.utcnow())

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = original_book
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()

    async def refresh_side_effect(book_instance):
        book_instance.updated_at = datetime.utcnow()
        return None
    mock_db_session.refresh = AsyncMock(side_effect=refresh_side_effect)

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    update_data = {"title": "Updated Title Only"} # No summary field

    with patch('routes.generate_book_summary', AsyncMock()) as mock_gen_summary, \
         patch('routes.log_action', AsyncMock()) as mock_log_action:

        response = client.put(f"/api/v1/books/{book_id}", json=update_data, auth=("testuser", "testpass"))

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["title"] == "Updated Title Only"
        assert response_data["summary"] == "Original Summary" # Summary should not change

        mock_gen_summary.assert_not_called() # generate_book_summary should NOT be called
        mock_log_action.assert_awaited_once()

    app.dependency_overrides = {}

def test_update_book_not_found():
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 999 # Non-existent ID

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None # Book not found
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    update_data = {"title": "Updated Title"}
    with patch('routes.log_action', AsyncMock()) as mock_log_action:
        response = client.put(f"/api/v1/books/{book_id}", json=update_data, auth=("testuser", "testpass"))

        assert response.status_code == 404
        assert f"Book with ID {book_id} not found" in response.json()["detail"]
        mock_log_action.assert_awaited_once()

    app.dependency_overrides = {}

# Tests for DELETE /books/{book_id}
def test_delete_book_success():
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 1

    mock_book_to_delete = Book(id=book_id, title="To Be Deleted", author="Author D", genre="Horror", year_published=2019, summary="Summary D", created_at=datetime.utcnow(), updated_at=datetime.utcnow())

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_book_to_delete
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.delete = AsyncMock() # Mock the delete method
    mock_db_session.commit = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch('routes.log_action', AsyncMock()) as mock_log_action:
        response = client.delete(f"/api/v1/books/{book_id}", auth=("testuser", "testpass"))

        assert response.status_code == 200
        assert response.json() == {"message": "Book deleted successfully"}

        mock_db_session.execute.assert_called_once()
        assert mock_db_session.delete.call_count == 1 # Check that delete was called
        mock_db_session.commit.assert_called_once()
        mock_log_action.assert_awaited_once()

    app.dependency_overrides = {}

def test_delete_book_not_found():
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 999 # Non-existent ID

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None # Book not found
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch('routes.log_action', AsyncMock()) as mock_log_action:
        response = client.delete(f"/api/v1/books/{book_id}", auth=("testuser", "testpass"))

        assert response.status_code == 404
        assert f"Book with ID {book_id} not found" in response.json()["detail"]
        mock_log_action.assert_awaited_once()

    app.dependency_overrides = {}

def test_delete_book_db_error_on_find():
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 1

    mock_db_session.execute = AsyncMock(side_effect=Exception("DB error finding book"))

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch('routes.log_action', AsyncMock()) as mock_log_action:
        response = client.delete(f"/api/v1/books/{book_id}", auth=("testuser", "testpass"))

        assert response.status_code == 500
        assert "Error deleting book" in response.json()["detail"]
        mock_log_action.assert_awaited_once()

    app.dependency_overrides = {}

def test_delete_book_db_error_on_commit():
    mock_db_session = AsyncMock()
    mock_user_id = 123
    book_id = 1

    mock_book_to_delete = Book(id=book_id, title="To Be Deleted", author="Author D", genre="Horror", year_published=2019, summary="Summary D", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_book_to_delete
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.delete = MagicMock() # Synchronous mock for delete
    mock_db_session.commit = AsyncMock(side_effect=Exception("DB error on commit")) # Error on commit

    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[verify_auth] = lambda: mock_user_id

    with patch('routes.log_action', AsyncMock()) as mock_log_action:
        response = client.delete(f"/api/v1/books/{book_id}", auth=("testuser", "testpass"))

        assert response.status_code == 500
        assert "Error deleting book" in response.json()["detail"]
        mock_log_action.assert_awaited_once()
        mock_db_session.rollback.assert_awaited_once() # Ensure rollback was called

    app.dependency_overrides = {}