"""
Test suite validating AI-driven connector synthesis and Zero-KTLO schema drift detection.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_connector_synthesis(client: AsyncClient):
    # Sample third-party payload from an external SaaS app (e.g. Okta / BambooHR style)
    third_party_payload = {
        "work_email": "john.doe@company.org",
        "given_name": "John",
        "family_name": "Doe",
        "job_title": "Principal Architect",
        "cost_center": "Core Infrastructure",
        "hire_date": "2024-01-15T09:00:00Z",
        "custom_slack_handle": "@johnd"
    }

    resp = await client.post(
        "/api/v2/tools/synthesize-connector",
        json=third_party_payload
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_entity"] == "rippling_hris_employee_v2"
    assert data["compatibility_score"] >= 0.60
    
    # Check that mappings were correctly identified
    mappings = {m["target_field"]: m["source_field"] for m in data["mappings"]}
    assert mappings["email"] == "work_email"
    assert mappings["first_name"] == "given_name"
    assert mappings["last_name"] == "family_name"
    assert mappings["title"] == "job_title"
    assert mappings["department"] == "cost_center"
    assert "custom_slack_handle" in data["unmapped_fields"]


@pytest.mark.asyncio
async def test_schema_drift_detection(client: AsyncClient):
    expected_schema = {
        "type": "object",
        "properties": {
            "api_key": {"type": "string"},
            "webhook_url": {"type": "string"},
            "retry_limit": {"type": "integer"}
        },
        "required": ["api_key", "webhook_url"]
    }

    # Observed payload is missing "webhook_url" and sends "retry_limit" as string
    observed_drifted_payload = {
        "api_key": "secret-live-token",
        "retry_limit": "5",  # Type conflict: string instead of integer
        "unregistered_new_field": "unexpected"
    }

    resp = await client.post(
        "/api/v2/tools/detect-schema-drift",
        json={
            "expected_schema": expected_schema,
            "observed_payload": observed_drifted_payload
        }
    )
    assert resp.status_code == 200
    report = resp.json()
    assert report["has_breaking_changes"] is True
    assert "webhook_url" in report["missing_required_fields"]
    assert report["risk_level"] == "HIGH"
    assert len(report["type_conflicts"]) == 1
    assert report["type_conflicts"][0]["field"] == "retry_limit"
