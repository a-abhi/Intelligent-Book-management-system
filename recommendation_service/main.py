import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from routes import recommendation_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Recommendation Service",
    description="Service for managing user preferences and book recommendations",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recommendation_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


@app.get("/")
async def root():
    """Root endpoint returning basic API information."""
    return {
        "message": "Welcome to the Recommendation Service API",
        "version": "1.0.0",
        "docs_url": "/docs",
    }
