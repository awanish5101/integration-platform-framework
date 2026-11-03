"""
Test suite validating distributed idempotency guarantees in API V2 mutations.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_idempotent_retry_returns_cached_response(client: AsyncClient):
    tenant = "tenant_idempotency"
    key = "idem_key_unique_001"
    payload = {
        "first_name": "Idempotent",
        "last_name": "Candidate",
        "email": "idempotent@rippling.com",
        "title": "Systems Engineer"
    }

    # Initial Request -> MISS
    resp1 = await client.post(
        "/api/v2/employees",
        json=payload,
        headers={"X-Tenant-ID": tenant, "X-Idempotency-Key": key}
    )
    assert resp1.status_code == 201
    assert resp1.headers.get("X-Cache-Lookup") == "MISS"
    data1 = resp1.json()

    # Retry Request with same key and payload -> HIT with exact same response body
    resp2 = await client.post(
        "/api/v2/employees",
        json=payload,
        headers={"X-Tenant-ID": tenant, "X-Idempotency-Key": key}
    )
    assert resp2.status_code == 201
    assert resp2.headers.get("X-Cache-Lookup") == "HIT"
    data2 = resp2.json()
    assert data1["employee_id"] == data2["employee_id"]


@pytest.mark.asyncio
async def test_idempotent_key_conflict_different_payload(client: AsyncClient):
    tenant = "tenant_idempotency_conflict"
    key = "idem_key_conflict_002"

    # Request 1
    await client.post(
        "/api/v2/employees",
        json={
            "first_name": "First",
            "last_name": "Test",
            "email": "first@example.com",
            "title": "Dev"
        },
        headers={"X-Tenant-ID": tenant, "X-Idempotency-Key": key}
    )

    # Request 2 with same key but altered payload -> 422 Unprocessable Entity
    resp2 = await client.post(
        "/api/v2/employees",
        json={
            "first_name": "CompletelyDifferent",
            "last_name": "Payload",
            "email": "different@example.com",
            "title": "Architect"
        },
        headers={"X-Tenant-ID": tenant, "X-Idempotency-Key": key}
    )
    assert resp2.status_code == 422
    assert "Idempotency key reused with different request payload" in resp2.json()["detail"]
