from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_status_check():
    response = client.get("/v1/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "Service is up and running!"}
