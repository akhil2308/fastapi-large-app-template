from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_status_check():
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "healthy"
    assert json_response["service"] == "up and running"
