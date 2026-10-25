import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db

@pytest.mark.asyncio
async def test_health_endpoint():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_plans_endpoint():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/v1/billing/plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) == 3
        assert data["plans"][0]["id"] == "starter"
        assert data["plans"][1]["id"] == "pro"
        assert data["plans"][2]["id"] == "enterprise"

@pytest.mark.asyncio
async def test_landing_page():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert "OmniExtract" in response.text
        assert "Playground" in response.text

@pytest.mark.asyncio
async def test_admin_manual_key_generation():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"X-Admin-Key": "dev_admin_secret_key_1234567890"}
        response = await ac.post(
            "/v1/admin/keys",
            json={"tier": "pro", "customer_email": "vip_client@agency.com", "monthly_limit": 50000},
            headers=headers
        )
        assert response.status_code == 200
        key = response.json()["key"]
        assert key.startswith("omni_pro_")

        # Now verify key usage endpoint
        usage_res = await ac.get(f"/v1/usage?key={key}")
        assert usage_res.status_code == 200
        usage_data = usage_res.json()
        assert usage_data["tier"] == "pro"
        assert usage_data["monthly_limit"] == 50000
        assert usage_data["requests_this_month"] == 0

@pytest.mark.asyncio
async def test_scrape_api_call():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test scraping with a public reliable URL (e.g. example.com)
        response = await ac.post(
            "/v1/scrape",
            json={"url": "https://example.com"}
        )
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["success"] is True
        assert "Example Domain" in res_data["data"]["title"] or "Example Domain" in res_data["data"]["markdown"]
        assert "tokens_markdown" in res_data["data"]
