import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    # This will be updated once the FastAPI app is scaffolded
    # from app.main import app
    # async with AsyncClient(app=app, base_url="http://test") as ac:
    #     yield ac
    yield None

@pytest.fixture
def mock_lead_data():
    return {
        "company_name": "Test Company",
        "company_domain": "test.com",
        "industry": "Software",
        "employee_count": 100,
        "status": "discovered",
        "source": "manual"
    }
