from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import asyncpg
from utils.logging import logger

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "llama3_db")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

async def get_db():
    """Dependency for getting async database sessions."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize the database on startup."""
    try:
        # Extract database name from URL
        db_name = DATABASE_URL.split("/")[-1]
        
        # Connect to PostgreSQL without specifying database
        sys_conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )
        
        # Check if database exists
        exists = await sys_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            db_name
        )
        
        if not exists:
            await sys_conn.execute(f'CREATE DATABASE "{db_name}"')
        
        await sys_conn.close()
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise 