"""
Test suite validating token bucket rate limiting and 429 throttling headers.
"""
import pytest
from httpx import AsyncClient
from app.core.rate_limiter import rate_limiter


@pytest.mark.asyncio
async def test_rate_limiter_throttling_and_headers(client: AsyncClient):
    tenant = "tenant_throttled"
    # Artificially set a low capacity bucket to verify 429 response
    rate_limiter.burst_capacity = 2
    rate_limiter.reset()

    # Request 1 -> Allowed
    r1 = await client.get("/api/v2/employees", headers={"X-Tenant-ID": tenant})
    assert r1.status_code == 200

    # Request 2 -> Allowed
    r2 = await client.get("/api/v2/employees", headers={"X-Tenant-ID": tenant})
    assert r2.status_code == 200

    # Request 3 -> Exceeded (429 Too Many Requests)
    r3 = await client.get("/api/v2/employees", headers={"X-Tenant-ID": tenant})
    assert r3.status_code == 429
    assert "Retry-After" in r3.headers
    assert r3.headers["X-RateLimit-Remaining"] == "0"
