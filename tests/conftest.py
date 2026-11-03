"""
Pytest configuration and shared fixtures.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.storage.repository import InMemoryRepository
import app.storage.repository as repo_module
from app.core.rate_limiter import rate_limiter
from app.core.idempotency import idempotency_manager


@pytest.fixture(autouse=True)
def reset_state():
    """Resets memory repository, rate limiters, and idempotency store before each test."""
    repo_module.repo = InMemoryRepository()
    rate_limiter.reset()
    idempotency_manager._store.clear()
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
