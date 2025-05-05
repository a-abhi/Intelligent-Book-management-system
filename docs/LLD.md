# Intelligent Book Management System - Low-Level Design (LLD)

## 1. **Overview**

This document provides the **Low-Level Design (LLD)** for the Intelligent Book Management System described in the [HLD](https://github.com/a-abhi/Intelligent-Book-management-system/blob/main/ERD-HLD.md). It outlines the internal structures, classes, modules, database schemas, and service contracts to implement the described functionality efficiently.

---

## 2. **Service Overview**

The system comprises multiple microservices, each handling a specific domain:

- **Book Service**: Manages book-related operations.
- **Review Service**: Handles CRUD operations for reviews.
- **Recommendation Service**: Generates book recommendations based on user preferences.
- **LLaMA3 Service**: Provides AI-generated summaries for books and reviews.
- **Shared Service**: Manages authentication (currently Basic Auth) and logging.
  
Each service communicates with other services via RESTful APIs and asynchronous messaging as required. Services interact with PostgreSQL databases for storing books, reviews, preferences, and logs.

---

## 3. **Detailed Design**

### 3.1 **Book Service**

**Responsibilities:**
- Handles CRUD operations for books.
- Interfaces with the database to store and retrieve book information.
- Calls the **Shared Service** for authentication and logging.

**Endpoints:**
- `POST /books`: Adds a new book.
  - **Request Body**: `{ title, author, genre, year_published, summary }`
  - **Headers**: `Authorization: Basic <base64(username:password)>`
  - **Response**: `{ id, title, author, genre, year_published, summary }`
- `GET /books`: Retrieves a list of all books.
  - **Headers**: `Authorization: Basic <base64(username:password)>`
  - **Response**: `[ { id, title, author, genre, year_published, summary }, ... ]`
- `GET /books/{id}`: Retrieves a specific book by ID.
  - **Headers**: `Authorization: Basic <base64(username:password)>`
  - **Response**: `{ id, title, author, genre, year_published, summary }`
- `PUT /books/{id}`: Updates a book's information.
  - **Request Body**: `{ title, author, genre, year_published, summary }`
  - **Headers**: `Authorization: Basic <base64(username:password)>`
  - **Response**: `{ id, title, author, genre, year_published, summary }`
- `DELETE /books/{id}`: Deletes a book by ID.
  - **Headers**: `Authorization: Basic <base64(username:password)>`
  - **Response**: `{ message: "Book deleted successfully." }`

**Core Classes**:

```python
class Book(Base):
    __tablename__ = 'books'
    id = Column(UUID, primary_key=True, default=uuid4)
    title = Column(String, nullable=False)
    author = Column(String)
    genre = Column(String)
    year_pub = Column(Integer)
    summary = Column(Text)

class BookService:
    async def create_book(self, book_data): ...
    async def get_book(self, book_id): ...
    async def update_book(self, book_id, updates): ...
    async def delete_book(self, book_id): ...
```
---

### 3.2 **Review Service**

**Responsibilities:**
- Handles CRUD operations for reviews.
- Interfaces with the **Book Service** to fetch book data and store reviews.
- Interfaces with the **Shared Service** for authentication and logging.

**Endpoints:**
- `POST /books/{id}/reviews`: Adds a new review for a book.
  - **Request Body**: `{ user_id, review_text, rating }`
  - **Headers**: `Authorization: Basic <base64(username:password)>`
  - **Response**: `{ review_id, book_id, user_id, review_text, rating }`
- `GET /books/{id}/reviews`: Retrieves all reviews for a book.
  - **Headers**: `Authorization: Basic <base64(username:password)>`
  - **Response**: `[ { review_id, user_id, review_text, rating }, ... ]`

**Core Classes**:

```python
class Review(Base):
    __tablename__ = 'reviews'
    id = Column(UUID, primary_key=True, default=uuid4)
    book_id = Column(UUID, ForeignKey('books.id'))
    user_id = Column(UUID)
    rating = Column(Integer)
    text = Column(Text)

class ReviewService:
    async def add_review(self, review_data): ...
    async def get_reviews_by_book(self, book_id): ...
```
---

### 3.3 **Recommendation Service**

**Responsibilities:**
- Generates book recommendations based on user preferences.
- Fetches data from the **Preferences Service** and **Books Service**.
- Interfaces with the **Shared Service** for authentication and logging.

**Endpoints:**
- `GET /recommendations`: Returns a list of book recommendations based on user preferences.
  - **Query Parameters**: `{ user_id }`
  - **Headers**: `Authorization: Basic <base64(username:password)>`
  - **Response**: `[ { id, title, author, genre, year_published }, ... ]`

**Core Classes**:

```python
class Preference(Base):
    __tablename__ = 'preferences'
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID)
    genre = Column(String)

class RecommendationService:
    async def get_recommendations(self, user_id): ...
```
---

### 3.4 **LLaMA3 AI Service**

**Responsibilities:**
- Generates summaries for books and reviews.
- Interfaces with the **Shared Service** for logging.
- Uses the locally running LLaMA3 model for content summarization.

**Endpoints:**
- `POST /generate-summary`: Generates a summary for a given book content or review.
  - **Request Body**: `{ content }`
  - **Headers**: `Authorization: Basic <base64(username:password)>`
  - **Response**: `{ summary }`

**Core Functions**:

```python
async def generate_summary(text: str) -> str:
    if cached(text):
        return get_from_cache(text)
    response = llama3_model.generate(text)
    save_to_cache(text, response)
    return response
```

---

### 3.5 **Shared Service**

**Responsibilities:**
- Provides authentication (currently Basic Auth, future JWT-based).
- Manages user logging for auditing purposes.
- Interacts with the **User Database** and **Log Database**.

**Endpoints:**
- `POST /auth/login`: Handles user login.
  - **Request Body**: `{ username, password }`
  - **Response**: `{ user_id }`

- `POST /auth/register` - Register
  - **Request Body**: `{ username, email,password }`
  - **Response**: `{ user_id }`

- `POST /logs` - Record user logs
  - **Request Body**: `{ user_id, service, action, status }`
  - **Response**: `{ log_id }`

**Core Classes**:

```python
class User(Base):
    __tablename__ = 'users'
    id = Column(UUID, primary_key=True, default=uuid4)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)

class Log(Base):
    __tablename__ = 'logs'
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID)
    service = Column(String)
    action = Column(String)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AuthService:
    def login(self, credentials): ...
    def register(self, user_data): ...

class Logger:
    async def log_action(self, log_data): ...
```
---

### 3.6 **Logging Mechanism**

The **Shared Service** logs all user actions for auditing. Each microservice will send a request to the **Shared Service** to log the action. This is done asynchronously to avoid blocking the main service flow.

**Logging Workflow:**
1. The target service (e.g., Book Service) receives a request.
2. The service validates the authentication using the **Shared Service**.
3. The service performs the requested operation (e.g., adding a book).
4. After the operation completes, the service sends an asynchronous request to the **Shared Service** to log the action (e.g., "Book Added").
5. The **Shared Service** records the log in the database.


## 4. **Database Design**

- **Books Table:**
  - Columns: `id (PK)`, `title`, `author`, `genre`, `year_published`, `summary`
- **Reviews Table:**
  - Columns: `id (PK)`, `book_id (FK)`, `user_id (FK)`, `review_text`, `rating`
- **Preferences Table:**
  - Columns: `id (PK)`, `user_id (FK)`, `genre`
- **Users Table:**
  - Columns: `id (PK)`, `username`, `email`, `password`
- **Logs Table:**
  - Columns: `id (PK)`, `user_id (FK)`, `service`, `action`, `status`, `timestamp`

---

## 5. **Error Handling & Validation**

- **Validation**:
  - All incoming data for CRUD operations (books, reviews) is validated.
  - User credentials are validated for login, ensuring they exist in the **Users** table.
  - Invalid inputs result in a `400 Bad Request` response.
  
- **Error Handling**:
  - If an error occurs while interacting with the database or AI model, a `500 Internal Server Error` is returned.
  - All errors are logged in the **Logs** table for auditing and troubleshooting.

---

## 7. **Scalability Considerations**

- **Microservices**: Services are designed to scale independently, allowing each service to be scaled horizontally based on its load.
- **Database**: PostgreSQL is used, and read replicas can be implemented to handle increased read traffic.
- **AI Service**: LLaMA3 can be scaled by running it on multiple instances, especially for resource-intensive summarization tasks.
- **Caching**: Use of Redis or similar caching mechanisms for frequently accessed data like book details and AI summaries to improve performance.

---

## 8. Unit Testing

* Pytest-based test suites
* Fixtures for DB mocking
* Async client tests for API endpoints

---

## 9. **Future Enhancements**

- **JWT-based Authentication**: Transition to JWT for stateless authentication.
- **Rate Limiting**: Implement rate limiting to prevent abuse of the API.
- **Caching Layer**: Introduce Redis to cache common queries and reduce load on the database.
- **User Personalization**: Introduce machine learning models to offer more personalized book recommendations.
