# Intelligent Book Management System

A microservices-based book management system with intelligent features including book summaries, reviews, and personalized recommendations.

## System Architecture

The system consists of four microservices:

1. **Book Service**
   - Manages book information and metadata
   - Handles CRUD operations for books
   - Provides book search functionality

2. **Review Service**
   - Manages book reviews and ratings
   - Integrates with LLaMA3 for review summarization
   - Provides review analytics

3. **LLaMA3 Service**
   - Generates book summaries using LLaMA3 model
   - Provides review summarization

4. **Recommendation Service**
   - Generates personalized book recommendations
   - Uses user preferences

## Prerequisites

- Python 3.8+
- PostgreSQL
- Docker (optional)
- LLaMA3 API access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/intelligent-book-management.git
cd intelligent-book-management
```

2. Create virtual environments for each service:
```bash
# For each service directory
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
# For each service
pip install -r requirements.txt
```

## Running the Services

1. Start the database:
```bash
docker-compose up -d postgres
```

2. Run each service:
```bash
# Book Service
cd book_service
uvicorn main:app --reload --port 8000

# Review Service
cd review_service
uvicorn main:app --reload --port 8001

# LLaMA3 Service
cd llama3_service
uvicorn main:app --reload --port 8002

# Recommendation Service
cd recommendation_service
uvicorn main:app --reload --port 8003
```

## API Documentation

Each service provides its own API documentation at:
- Book Service: http://localhost:8000/docs
- Review Service: http://localhost:8001/docs
- LLaMA3 Service: http://localhost:8002/docs
- Recommendation Service: http://localhost:8003/docs

## Testing

Run tests for each service:
```bash
# For each service directory
pytest
```

Run tests with coverage:
```bash
pytest --cov=.
```

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
