# Intelligent Book Management System - ERD & High-Level Design

## 1. ERD-HLD Abstract
We're building a cloud-based Intelligent Book Management System that leverages AI to make book management smarter and more efficient. Think of it as your digital librarian that not only keeps track of books but also helps you discover new ones and understand them better through AI-powered features. The system will expose RESTful APIs for everything from user management to book recommendations, built with scalability and security in mind.

## 2. Engineering Requirements

### 2.1 Functional Requirements

#### 2.1.1 In-Scope Requirements
1. Book Management
   - CRUD operations for books (add, update, delete, and retrieve books)
   - Store and manage book metadata (title, author, genre, publication year)
   - Handle book summaries and their retrieval

2. Review Management
   - Let users add and manage their book reviews
   - Retrieve and display book reviews with proper pagination

3. AI Features
   - Generate concise book summaries
   - Create review summaries to give quick insights
   - Provide personalized book recommendations

4. User Management
   - User registration and profile management
   - Basic authentication
   - Role-based access (admin vs regular users)

5. API Endpoints
   - RESTful API design following best practices
   - Input validation and sanitization
   - Proper error handling and meaningful messages
   - Rate limiting to prevent abuse

#### 2.1.2 Out-of-Scope Requirements
1. User Interface
   - Web frontend development
   - Mobile application development
2. Any other features not explicitly mentioned above

### 2.2 Non-Functional Requirements

#### 2.2.1 Scalability
- Support for horizontal scaling as user base grows
- Database read replicas for better read performance
- Redis caching for frequently accessed data
- Load balancing to distribute traffic

#### 2.2.2 Security
- Secure password hashing using bcrypt
- Input validation and sanitization
- Database encryption at rest
- HTTPS for all API endpoints

#### 2.2.3 Maintainability
- Clean, modular code structure
- Comprehensive API documentation
- Unit test coverage > 80%
- Automated CI/CD pipeline

## 3. High-Level Design

### 3.1 Component Diagram
![alt text](https://github.com/a-abhi/Intelligent-Book-management-system/blob/main/architectureDiagram.jpg?raw=true)

### 3.2 Component Details

#### 3.2.1 API Gateway Layer
- **Request Validator**: Ensures all incoming requests are properly formatted and contain valid data
- **Rate Limiter**: Prevents abuse by limiting requests per user/IP
- **Load Balancer**: Distributes traffic across multiple instances

#### 3.2.2 Application Layer
- **Book Service**: Manages all book-related operations
- **Review Service**: Handles review creation, updates, and retrieval
- **AI Service**: Manages AI model operations and inference
- **Auth Service**: Handles user authentication and session management

#### 3.2.3 Data Layer
- **PostgreSQL**: Our primary database for storing all structured data
- **Redis Cache**: Handles caching of frequently accessed data
- **AI Model Storage**: Stores and serves our AI models

### 3.3 Workflows

#### 3.3.1 Book Management Flow
1. Client sends request to API Gateway
2. Request is validated and authenticated
3. Book Service processes the request
4. Database operations are performed
5. Response is returned to client

#### 3.3.2 Review Management Flow
1. Client submits a review
2. Review Service processes the request
3. Database is updated
4. AI Service generates a summary if needed
5. Response is returned to client

#### 3.3.3 AI Feature Flow
1. Client requests a summary or recommendation
2. AI Service processes the request
3. Llama3 model generates the response
4. Response is cached for future similar requests
5. Response is returned to client

### 3.4 Back of the Envelope Estimation

#### 3.4.1 Load Estimation
- Expected users: 1,000-5,000 (conservative estimate for POC)
- Daily active users: ~20% = 200-1,000 users
- Average requests per user per day: 10
- Total daily requests: 2,000-10,000
- Peak requests per second: ~5-10 (assuming 80/20 rule)

#### 3.4.2 Storage Estimation
- Books: 10,000 books × 50KB metadata = 500MB
- Reviews: 50,000 reviews × 2KB = 100MB
- User data: 5,000 users × 5KB = 25MB
- AI models: ~2GB
- Total storage: ~3GB (with 2x buffer = 6GB)

### 3.5 Scalability

#### 3.5.1 Horizontal Scaling
- Microservices architecture allows independent scaling
- Load balancing across multiple instances
- Auto-scaling based on CPU/memory metrics

#### 3.5.2 Database Scaling
- Read replicas for better read performance
- Connection pooling to manage database connections
- Query optimization and proper indexing

#### 3.5.3 Caching Strategy
- Redis for caching frequent queries
- Database query result caching
- API response caching with proper TTL

### 3.6 Performance

#### 3.6.1 Optimization Techniques
- Database indexing on frequently queried fields
- Query optimization and proper joins
- Connection pooling to reduce overhead
- Response caching for static data

#### 3.6.2 Monitoring
- Track key performance metrics
- Monitor response times
- Watch resource utilization
- Track error rates and types

### 3.7 Security

#### 3.7.1 Authentication
- Basic authentication
- Password hashing
- Role-based access
