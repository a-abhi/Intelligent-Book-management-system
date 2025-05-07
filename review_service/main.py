from fastapi import FastAPI
from routes import router
from models import Base
from db import engine, DATABASE_URL
import asyncpg
import os

app = FastAPI(title="Review Service")

@app.on_event("startup")
async def init_db():
    # Extract database name from DATABASE_URL
    db_name = DATABASE_URL.split("/")[-1]
    # Create a connection to postgres without specifying a database
    sys_conn = await asyncpg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )
    
    # Check if database exists
    exists = await sys_conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1", db_name
    )
    
    if not exists:
        # Create database if it doesn't exist
        await sys_conn.execute(f'CREATE DATABASE "{db_name}"')
    
    await sys_conn.close()
    
    # Now create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(router, prefix="/api/v1") 