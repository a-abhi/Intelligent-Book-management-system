# Intelligent Book Management System - Low-Level Design

## 1. Database Schema

### 1.1 Books Table
```sql
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    genre VARCHAR(100) NOT NULL,
    year_published INTEGER NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_books_author ON books(author);
CREATE INDEX idx_books_genre ON books(genre);
```

### 1.2 Reviews Table
```sql
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    review_text TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reviews_book_id ON reviews(book_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
```

### 1.3 Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

## 2. API Endpoints Implementation

### 2.1 Book Management Endpoints

#### 2.1.1 Create Book
```python
@router.post("/books", response_model=BookResponse)
async def create_book(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_book = Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book
```

#### 2.1.2 Get Book
```python
@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
```

### 2.2 Review Management Endpoints

#### 2.2.1 Create Review
```python
@router.post("/books/{book_id}/reviews", response_model=ReviewResponse)
async def create_review(
    book_id: int,
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_review = Review(
        book_id=book_id,
        user_id=current_user.id,
        **review.dict()
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review
```

### 2.3 AI Feature Endpoints

#### 2.3.1 Generate Summary
```python
@router.post("/generate-summary")
async def generate_summary(
    content: str,
    ai_service: AIService = Depends(get_ai_service)
):
    summary = await ai_service.generate_summary(content)
    return {"summary": summary}
```

## 3. Class Diagrams

### 3.1 Book Service
```python
class BookService:
    def __init__(self, db: Session):
        self.db = db

    async def create_book(self, book_data: dict) -> Book:
        pass

    async def get_book(self, book_id: int) -> Book:
        pass

    async def update_book(self, book_id: int, book_data: dict) -> Book:
        pass

    async def delete_book(self, book_id: int) -> bool:
        pass
```

### 3.2 Review Service
```python
class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    async def create_review(self, review_data: dict) -> Review:
        pass

    async def get_book_reviews(self, book_id: int) -> List[Review]:
        pass

    async def get_average_rating(self, book_id: int) -> float:
        pass
```

### 3.3 AI Service
```python
class AIService:
    def __init__(self, model_path: str):
        self.model = self.load_model(model_path)
        self.cache = RedisCache()

    async def generate_summary(self, content: str) -> str:
        pass

    async def get_recommendations(self, user_id: int) -> List[Book]:
        pass
```

## 4. Authentication Implementation

### 4.1 JWT Authentication
```python
class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
```

## 5. Caching Implementation

### 5.1 Redis Cache
```python
class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[str]:
        return await self.redis.get(key)

    async def set(self, key: str, value: str, expire: int = 3600):
        await self.redis.set(key, value, ex=expire)
```

## 6. Error Handling

### 6.1 Custom Exceptions
```python
class BookNotFoundError(Exception):
    pass

class ReviewValidationError(Exception):
    pass

class AIServiceError(Exception):
    pass
```

### 6.2 Error Handler
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, BookNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": "Book not found"}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

## 7. Testing Implementation

### 7.1 Unit Tests
```python
class TestBookService:
    @pytest.fixture
    def book_service(self):
        return BookService()

    async def test_create_book(self, book_service):
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023
        }
        book = await book_service.create_book(book_data)
        assert book.title == book_data["title"]
```

### 7.2 Integration Tests
```python
class TestBookAPI:
    async def test_create_book(self, client):
        response = await client.post(
            "/books",
            json={
                "title": "Test Book",
                "author": "Test Author",
                "genre": "Fiction",
                "year_published": 2023
            }
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Test Book"
```

## 8. Logging Implementation

### 8.1 Logger Configuration
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### 8.2 Logging Usage
```python
@router.post("/books")
async def create_book(book: BookCreate):
    logger.info(f"Creating new book: {book.title}")
    try:
        result = await book_service.create_book(book)
        logger.info(f"Book created successfully: {result.id}")
        return result
    except Exception as e:
        logger.error(f"Error creating book: {str(e)}")
        raise
``` 