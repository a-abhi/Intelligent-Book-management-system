from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import shared_router
from models import Base
from db import engine

app = FastAPI(
    title="Shared Service",
    description="Service for shared functionality like authentication and logging",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Include routers
app.include_router(shared_router) 