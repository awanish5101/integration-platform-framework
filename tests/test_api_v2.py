"""
Test suite verifying standardized API V2 Employee records and pagination.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_and_readiness(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "HEALTHY"

    ready = await client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "READY"


@pytest.mark.asyncio
async def test_create_and_get_employee(client: AsyncClient):
    payload = {
        "first_name": "Awanish",
        "last_name": "Chaurasiya",
        "email": "avanish84ya@gmail.com",
        "department": "Platform Engineering",
        "title": "Software Engineer",
        "employment_status": "ACTIVE"
    }
    create_resp = await client.post(
        "/api/v2/employees",
        json=payload,
        headers={"X-Tenant-ID": "tenant_alpha"}
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["first_name"] == "Awanish"
    assert data["employee_id"].startswith("emp_")
    emp_id = data["employee_id"]

    # Retrieve employee
    get_resp = await client.get(
        f"/api/v2/employees/{emp_id}",
        headers={"X-Tenant-ID": "tenant_alpha"}
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "avanish84ya@gmail.com"

    # Multi-tenant isolation: different tenant cannot view
    other_tenant_resp = await client.get(
        f"/api/v2/employees/{emp_id}",
        headers={"X-Tenant-ID": "tenant_beta"}
    )
    assert other_tenant_resp.status_code == 404


@pytest.mark.asyncio
async def test_cursor_pagination(client: AsyncClient):
    tenant = "tenant_pagination"
    # Seed 5 employees
    for i in range(5):
        await client.post(
            "/api/v2/employees",
            json={
                "first_name": f"User_{i}",
                "last_name": "Test",
                "email": f"user{i}@rippling.com",
                "department": "Engineering",
                "title": "Engineer"
            },
            headers={"X-Tenant-ID": tenant}
        )

    # Page 1 (limit 2)
    p1 = await client.get(f"/api/v2/employees?limit=2", headers={"X-Tenant-ID": tenant})
    assert p1.status_code == 200
    d1 = p1.json()
    assert len(d1["data"]) == 2
    assert d1["pagination"]["next_cursor"] is not None
    next_cursor = d1["pagination"]["next_cursor"]

    # Page 2
    p2 = await client.get(f"/api/v2/employees?limit=2&cursor={next_cursor}", headers={"X-Tenant-ID": tenant})
    assert p2.status_code == 200
    d2 = p2.json()
    assert len(d2["data"]) == 2
    # Ensure distinct records
    assert d1["data"][0]["employee_id"] != d2["data"][0]["employee_id"]


@pytest.mark.asyncio
async def test_update_and_delete_employee(client: AsyncClient):
    tenant = "tenant_mutations"
    create_resp = await client.post(
        "/api/v2/employees",
        json={
            "first_name": "Initial",
            "last_name": "Name",
            "email": "initial@example.com",
            "title": "Junior Dev"
        },
        headers={"X-Tenant-ID": tenant}
    )
    emp_id = create_resp.json()["employee_id"]

    # Update
    update_resp = await client.put(
        f"/api/v2/employees/{emp_id}",
        json={"title": "Senior Software Engineer"},
        headers={"X-Tenant-ID": tenant}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Senior Software Engineer"

    # Delete
    del_resp = await client.delete(
        f"/api/v2/employees/{emp_id}",
        headers={"X-Tenant-ID": tenant}
    )
    assert del_resp.status_code == 204

    # Verify deleted
    get_resp = await client.get(
        f"/api/v2/employees/{emp_id}",
        headers={"X-Tenant-ID": tenant}
    )
    assert get_resp.status_code == 404
