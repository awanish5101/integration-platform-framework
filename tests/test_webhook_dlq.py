"""
Test suite validating Zero-KTLO Webhook delivery, exponential backoff, DLQ quarantine, and replay.
"""
import pytest
from httpx import AsyncClient
from app.services.webhook_dispatcher import webhook_dispatcher
from app.config import settings


@pytest.mark.asyncio
async def test_webhook_successful_dispatch(client: AsyncClient):
    # Test mock success endpoint
    tenant = "tenant_webhook_test"
    resp = await client.post(
        "/api/v2/tools/webhooks/dispatch?topic=employee.onboarded&target_url=mock://success",
        json={"employee_id": "emp_101", "name": "Jane Doe"},
        headers={"X-Tenant-ID": tenant}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "DELIVERED"
    assert data["attempts"] == 1
    assert data["last_status_code"] == 200


@pytest.mark.asyncio
async def test_webhook_quarantine_to_dlq(client: AsyncClient):
    tenant = "tenant_dlq_test"
    # Temporarily set fast backoff for instant test execution
    original_backoff = settings.WEBHOOK_BACKOFF_BASE_SECONDS
    settings.WEBHOOK_BACKOFF_BASE_SECONDS = 0.01

    try:
        # Mock fail target URL
        resp = await client.post(
            "/api/v2/tools/webhooks/dispatch?topic=employee.terminated&target_url=mock://fail",
            json={"employee_id": "emp_999"},
            headers={"X-Tenant-ID": tenant}
        )
        assert resp.status_code == 200
        event = resp.json()
        assert event["status"] == "FAILED_DLQ"
        assert event["attempts"] == 3
        event_id = event["event_id"]

        # Verify event appears in DLQ inspection endpoint
        dlq_resp = await client.get("/api/v2/tools/webhooks/dlq", headers={"X-Tenant-ID": tenant})
        assert dlq_resp.status_code == 200
        dlq_list = dlq_resp.json()
        assert any(e["event_id"] == event_id for e in dlq_list)

        # Replay event with mock success URL to verify recovery workflow
        event_obj = webhook_dispatcher.repo.get_webhook(event_id)
        event_obj.target_url = "mock://success"
        replay_resp = await client.post(
            "/api/v2/tools/webhooks/dlq/replay",
            json={"event_ids": [event_id]},
            headers={"X-Tenant-ID": tenant}
        )
        assert replay_resp.status_code == 200
        replayed = replay_resp.json()
        assert len(replayed) == 1
        assert replayed[0]["status"] == "DELIVERED"

    finally:
        settings.WEBHOOK_BACKOFF_BASE_SECONDS = original_backoff
