"""
Test suite validating App Shop / Marketplace discovery, installation, and lifecycle.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_browse_apps_and_search(client: AsyncClient):
    resp = await client.get("/api/v2/marketplace/apps")
    assert resp.status_code == 200
    apps = resp.json()
    assert len(apps) >= 3

    # Search by keyword
    slack_resp = await client.get("/api/v2/marketplace/apps?search=slack")
    assert slack_resp.status_code == 200
    slack_data = slack_resp.json()
    assert len(slack_data) == 1
    assert slack_data[0]["app_id"] == "slack-enterprise"

    # Filter by category
    it_resp = await client.get("/api/v2/marketplace/apps?category=IT_ADMIN")
    assert it_resp.status_code == 200
    assert all(a["category"] == "IT_ADMIN" for a in it_resp.json())


@pytest.mark.asyncio
async def test_app_install_lifecycle(client: AsyncClient):
    tenant = "tenant_acme_corp"
    
    # 1. Install without full required config -> PENDING_AUTH
    resp1 = await client.post(
        "/api/v2/marketplace/install",
        json={"app_id": "slack-enterprise"},
        headers={"X-Tenant-ID": tenant}
    )
    assert resp1.status_code == 201
    inst1 = resp1.json()
    assert inst1["status"] == "PENDING_AUTH"

    # 2. Configure app with required token -> CONFIGURED
    resp2 = await client.put(
        f"/api/v2/marketplace/installations/slack-enterprise/configure",
        json={"config_values": {"api_token": "xoxb-12345-verified"}},
        headers={"X-Tenant-ID": tenant}
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "CONFIGURED"

    # 3. List tenant integrations
    list_resp = await client.get("/api/v2/marketplace/installations", headers={"X-Tenant-ID": tenant})
    assert list_resp.status_code == 200
    installed_list = list_resp.json()
    assert len(installed_list) == 1
    assert installed_list[0]["app_id"] == "slack-enterprise"

    # 4. Uninstall
    uninst_resp = await client.delete(
        "/api/v2/marketplace/installations/slack-enterprise",
        headers={"X-Tenant-ID": tenant}
    )
    assert uninst_resp.status_code == 204

    # 5. Verify uninstalled
    list_after = await client.get("/api/v2/marketplace/installations", headers={"X-Tenant-ID": tenant})
    assert len(list_after.json()) == 0
