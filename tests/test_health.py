import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app

sync_client = TestClient(app)


def test_liveness():
    response = sync_client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_detailed_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "healthy"
    assert json_response["service"] == "up and running"
