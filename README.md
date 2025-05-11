# Intelligent Book Management System

A microservices-based book management system with intelligent features including book summaries, reviews, and personalized recommendations. The system leverages LLaMA3 for AI-powered features and provides a robust API for book management.

## System Architecture

The system consists of five microservices:

1. **Book Service** (Port: 8001)
   - Manages book information and metadata
   - Handles CRUD operations for books
   - Provides book search functionality
   - Integrates with LLaMA3 for book summaries

2. **Review Service** (Port: 8002)
   - Manages book reviews and ratings
   - Integrates with LLaMA3 for review summarization
   - Provides review analytics
   - Links reviews with books and users

3. **LLaMA3 Service** (Port: 8004)
   - Generates book summaries using LLaMA3 model
   - Provides review summarization
   - Integrates with Ollama for AI model access
   - Handles AI-powered text generation

4. **Recommendation Service** (Port: 8003)
   - Generates personalized book recommendations
   - Uses user preferences and reading history
   - Provides genre-based recommendations
   - Integrates with book and review services

5. **Shared Service** (Port: 8000)
   - Provides common functionality across services
   - Manages shared resources and utilities
   - Handles cross-service communication

## Prerequisites

- Python 3.8+
- PostgreSQL 15
- Docker and Docker Compose
- Ollama (for LLaMA3 integration)
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/intelligent-book-management.git
cd intelligent-book-management
```

2. Set up environment variables (optional):
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the setup script:
```bash
chmod +x setup_requirements.sh
./setup_requirements.sh
```

4. Start the services using Docker Compose:
```bash
docker-compose up -d
```

## Running the Services

### Using Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Manual Setup (Development)
1. Create virtual environments for each service:
```bash
# For each service directory
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
# For each service
pip install -r requirements.txt
```

3. Start PostgreSQL:
```bash
docker-compose up -d postgres
```

4. Run each service:
```bash
# Book Service
cd book_service
uvicorn main:app --reload --port 8001

# Review Service
cd review_service
uvicorn main:app --reload --port 8002

# LLaMA3 Service
cd llama3_service
uvicorn main:app --reload --port 8004

# Recommendation Service
cd recommendation_service
uvicorn main:app --reload --port 8003

# Shared Service
cd shared_service
uvicorn main:app --reload --port 8000
```

## API Documentation

Each service provides its own Swagger UI documentation at:
- Book Service: http://localhost:8001/docs
- Review Service: http://localhost:8002/docs
- LLaMA3 Service: http://localhost:8004/docs
- Recommendation Service: http://localhost:8003/docs
- Shared Service: http://localhost:8000/docs

## Testing

Run tests for each service:
```bash
# For each service directory
pytest

# Run tests with coverage
pytest --cov=.
```

## Continuous Integration

The project uses GitHub Actions for continuous integration. The CI workflow runs automatically on:
- Push to main branch
- Push to feature branches (f_*)
- Push to fix branches (fix_*)
- Pull requests to main branch

### CI Workflow Features

The CI pipeline includes the following steps for each service:
1. **Code Checkout**: Clones the repository
2. **Python Setup**: Configures Python 3.12
3. **Docker Compose**: Installs Docker Compose v2.35.1
4. **Code Linting**: Runs Flake8 for code quality checks
5. **Docker Build**: Builds service Docker images
6. **Testing**: Runs pytest in Docker containers

### Service Matrix
The CI runs in parallel for all services:
- Book Service
- LLaMA3 Service
- Recommendation Service
- Review Service
- Shared Service

### Viewing CI Results
- Check the "Actions" tab in the GitHub repository
- View detailed logs for each service's CI run
- Monitor test results and linting issues

## Project Structure

```
intelligent-book-management/
├── book_service/
│   ├── routes
│   ├── db
│   ├── models
│   ├── schemas
│   ├── tests/
│   └── utils/
│   └── main
├── review_service/
│   ├── routes
│   ├── db
│   ├── models
│   ├── schemas
│   ├── tests/
│   └── utils/
│   └── main
├── llama3_service/
│   ├── routes
│   ├── db
│   ├── models
│   ├── schemas
│   ├── tests/
│   └── utils/
│   └── main
├── recommendation_service/
│   ├── routes
│   ├── db
│   ├── models
│   ├── schemas
│   ├── tests/
│   └── utils/
│   └── main
└── docker-compose.yml
```

## Features

- **Book Management**
  - Add, update, and delete books
  - Search books by genre
  - Add AI generated summary at the time of Add book

- **Review System**
  - User reviews and ratings
  - Review summarization using LLaMA3

- **Intelligent Summaries**
  - AI-generated book summaries
  - Review summarization

- **Recommendations**
  - Personalized book recommendations
  - User preference learning
