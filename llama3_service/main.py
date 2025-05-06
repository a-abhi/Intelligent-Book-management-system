from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from db import init_db
import logging
from logging_utils import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLaMA3 Service",
    description="Service for generating book summaries using LLaMA3",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

@app.get("/")
async def root():
    return {
        "message": "Welcome to LLaMA3 Service",
        "docs": "/docs",
        "health": "/api/v1/health"
    } 