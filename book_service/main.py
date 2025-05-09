from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import book_router
from db import init_db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Book Service",
    description="Service for managing books and their summaries",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(book_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")

@app.get("/")
async def root():
    return {"message": "Welcome to the Book Service API"} 