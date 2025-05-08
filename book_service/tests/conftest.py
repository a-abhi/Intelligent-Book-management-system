import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from typing import AsyncGenerator

from book_service.routes import router as book_router

@pytest.fixture(scope="session")
def app() -> FastAPI:
    """
    Create a FastAPI app instance for testing.
    This fixture has a session scope, meaning it will be created once per test session.
    """
    _app = FastAPI()
    _app.include_router(book_router)
    return _app

@pytest.fixture(scope="function")
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an AsyncClient for making requests to the test app.
    This fixture has a function scope, meaning a new client is created for each test function.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
