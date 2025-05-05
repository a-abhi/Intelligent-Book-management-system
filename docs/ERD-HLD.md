# Intelligent Book Management System - ERD & High-Level Design

## 1. ERD-HLD Abstract
The **Intelligent Book Management System** is a cloud-native, scalable microservices-based solution designed to manage books, reviews, recommendations, and content summarization using a generative AI model (ollama3). It provides RESTful APIs to add, retrieve, and manage books and their reviews, while also integrating ollama3 for AI-generated summaries and personalized recommendations. The system is intended to support high availability, modular deployment, and efficient data processing using asynchronous programming and modern DevOps practices.

## 2. Engineering Requirements

### 2.1 Functional Requirements

#### 2.1.1 In-Scope Requirements
- Add, update, delete and retrieve books
- Submit and fetch reviews
- Generate personalized recommendations
- Provide AI-powered summaries
- Authenticate and authorize users
- Log all user actions for auditing

#### 2.1.2 Out-of-Scope Requirements
1. User Interface
2. Any other features not explicitly mentioned above

### 2.2 Non-Functional Requirements

- **Performance**: Support up to 1000 requests/sec with average latency <300ms
- **Scalability**: Microservices designed to scale horizontally
- **Availability**: 99.9% uptime with automated restarts and health checks
- **Security**: Basic authentication; encrypted connections
- **Maintainability**: Modular service structure with unit/integration tests
- **Extensibility**: New services can be added without major refactor

## 3. Back-of-the-Envelope Estimations

These estimations are derived based on assumed traffic patterns and service usage:

| Component          | Estimate                            | Assumptions                                      |
|-------------------|-------------------------------------|--------------------------------------------------|
| Books per day     | ~10,000 additions                   | 500 authors adding 20 books/day                  |
| Reviews per day   | ~100,000                            | 10K users submitting 10 reviews/day              |
| API RPS           | ~500–1000 requests/sec              | Assuming 50K DAUs with 1-2 requests/min each     |
| Storage (1 yr)    | ~50GB for books + 100GB reviews     | Books: 2KB each; Reviews: 1KB × volume           |
| AI Calls/Day      | ~50,000 summarization calls         | 50% reviews trigger summary generation           |
| LLaMA3 Latency    | ~800ms–1.5s per summary             | Based on avg LLaMA3 generation time              |

> Notes:
> - PostgreSQL can handle these loads with connection pooling and read replicas.
> - Shared Service is horizontally scalable for auth/log calls.
> - AI summary caching reduces redundant generation calls significantly.

## 4. High-Level Design

### 4.1 Component Diagram
![alt text](https://github.com/a-abhi/Intelligent-Book-management-system/blob/main/images/MicroserviceArchitecture.jpeg?raw=true)

### 4.2 Component Details

- **Book Service**: CRUD operations for books; calls Shared Service for auth + logging.
- **Review Service**: Manage reviews, ratings; integrates with Shared Service.
- **Recommendation Service**: Generates book suggestions; reads user preferences; checks auth.
- **LLaMA3 AI Service**: Generate summaries, review synthesis.
- **Shared Service**: Handles authentication, user management, and centralized logging.

## 5 Workflows

### 5.1 Sequence Diagram

![alt text](https://github.com/a-abhi/Intelligent-Book-management-system/blob/main/images/SequenceDiagram.jpeg?raw=true)

### 5.2 Service Interaction (Sequence)

1. Client hits API Gateway.
2. API Gateway routes to target service (e.g., Book Service).
3. Target service validates auth via Shared Service.
4. Upon success, executes DB operations.
5. Sends audit logs to Shared Service (async).

## 6 Entity Relationship Diagram (ERD)

### 6.1 Entities & Relationships
![alt text](https://github.com/a-abhi/Intelligent-Book-management-system/blob/main/images/ERD.jpeg?raw=true)

> Notes:
> - Each review is linked to one book. 
> - Preferences help in generating recommendations. 
> - Logs are used for auditing user actions and are recorded via the Shared Service.

## 7 Tech Stack

| Layer           | Tech                                 |
|-----------------|--------------------------------------|
| API             | FastAPI (async)                      |
| DB              | PostgreSQL (RDS on AWS)              |
| AI Model        | LLaMA3 via OLLama / HuggingFace      |
| Cloud Infra     | AWS ECS Fargate, S3, RDS, CloudWatch |
| Async DB        | SQLAlchemy Async + asyncpg           |
| Deployment      | Docker, Docker Compose, GitHub Actions |
| Monitoring      | Prometheus + Grafana (optional)      |


## 8 Scalability

- **Microservices**: Each domain (books, reviews, recommendations, AI, auth/logging) is isolated and can scale independently.
- **DB Scaling**: Read replicas for PostgreSQL; consider partitioning large review tables.
- **AI Model Scaling**: Run on separate CPU-enabled EC2 instances with queueing + caching.
- **Async APIs**: All APIs use `async/await` to handle concurrent requests efficiently.
- **Horizontal Scaling**: Each service container can scale using AWS ECS Fargate.
- **CI/CD**: Auto-deploy on Git push using GitHub Actions + AWS CodeDeploy.
- **Monitoring**: Prometheus + Grafana or CloudWatch for performance tracking.

## 9 Future Enhancements

- Implement **rate-limiting** and **caching layer** (e.g., Redis).
- Move LLaMA3 summaries to **event-driven architecture** (e.g., SQS, Kafka).
- Enable **streaming summaries** for long content using chunked responses.
- Extend shared service with **role-based access control**, **audit logging**, and centralized **configuration management**.
