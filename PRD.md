# Intelligent Book Management System - Product Requirements Document

## 1. Project Overview
The Intelligent Book Management System is a cloud-based application that leverages AI to provide an enhanced book management experience. The system allows users to manage books, generate AI-powered summaries, give ratings and reviews, summarize reviews, and receive personalized recommendations while maintaining a secure and scalable architecture.

## 2. Business Requirements
- Create a modular, scalable and maintainable book management system
- System Should be able to help users to add, update retrieve books from db
- Generate Summaries, recommend books based on user preferences, manage and generate user review summary via open source AI model
- Ensure secure access to the system via basic Auth
- Support cloud deployment for global accessibility
- Should be accessible via restfull API calls

## 3. Technical Requirements

### 3.1 Core Technologies
- **Backend Framework**: FastAPI/Flask (Python)
- **Database**: PostgreSQL
- **AI Model**: Llama3 (local deployment) or any open-source AI model
- **Cloud Platform**: AWS
- **Containerization**: Docker
- **Version Control**: Git
- **Caching**: Redis

### 3.2 Database Schema
#### Books Table
- id (Primary Key)
- title
- author
- genre
- year_published
- summary
- created_at (Timestamp)
- updated_at (Timestamp)

#### Reviews Table
- id (Primary Key)
- book_id (Foreign Key)
- user_id
- review_text
- rating
- created_at (Timestamp)
- updated_at (Timestamp)

#### Users Table
- id (Primary Key)
- username
- email
- password_hash
- role
- created_at (Timestamp)
- updated_at (Timestamp)

### 3.3 API Endpoints
1. Book Management
   - POST /books - Add new book
   - GET /books - Retrieve all books
   - GET /books/<id> - Get specific book by id
   - PUT /books/<id> - Update book by id
   - DELETE /books/<id> - Delete book by id

2. Review Management
   - POST /books/<id>/reviews - Add review for a book
   - GET /books/<id>/reviews - Get all reviews for the book
   - GET /books/<id>/reviews/summary - Get review summary (This api for generating reviews summary)

3. AI Features
   - GET /books/<id>/summary - Get book summary and aggregated rating for a book
   - GET /recommendations - Get personalized book recommendations based on user preferences
   - POST /generate-summary - Generate summary for given book content
   

4. User Management
   - POST /auth/register - Register new user
   

### 3.4 Asynchronous Programming
- Implement asyn operation for db operations and AI model (sqlalchemy[asyncio] and asyncpg)

### 3.5 Security Requirements
- Implement basic authentication
- Secure API endpoints
- Encrypted database connections
- Input validation and sanitization
- Rate limiting for API endpoints
- Password hashing and salting
- Request validation middleware

## 4. Development Requirements

### 4.1 Code Structure
- Modular and reusable components
- Clear separation of concerns
- Independent testable modules
- Proper package organization
- SOLID principles implementation
- Design Patterns
- Service layer for business logic
- Controller layer for request handling

### 4.2 Testing Requirements
- Unit tests for all modules
- Integration tests for API endpoints
- Automated test suite
- Test coverage documentation
- CI/CD pipeline integration

### 4.3 Documentation Requirements
- API documentation (Swagger)
- Setup and deployment instructions
- Code documentation
- Testing procedures
- Architecture diagrams
- Database schema documentation
- API usage examples
- Troubleshooting guide

## 5. Deployment Requirements

### 5.1 Cloud Infrastructure (AWS)
- EC2/Lambda/ECS for application hosting
- RDS for PostgreSQL database
- S3 for model file storage
- ElastiCache for caching (Bonus)
- SageMaker for ML model deployment (Bonus)

### 5.2 Deployment Options (Any one)
1. GitHub repository with detailed instructions
2. Docker containerization
3. CI/CD workflow documentation
4. AWS deployment with free tier
