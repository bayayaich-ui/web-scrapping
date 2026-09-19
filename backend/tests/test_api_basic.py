from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_url_is_rejected_before_database_access():
    response = TestClient(app).post("/api/scrape", json={"url": "file:///tmp/data.html"})
    assert response.status_code == 422
