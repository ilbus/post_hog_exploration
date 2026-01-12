from fastapi.testclient import TestClient
from src.api.main import app
from src.config import settings

client = TestClient(app)

def test_health_check_ish():
    # Since we don't have a /health endpoint, let's just check 404 on root
    response = client.get("/")
    assert response.status_code == 404

def test_ingest_no_auth():
    response = client.post("/ingest", json={"event": "test"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing API Key"}

def test_ingest_invalid_auth():
    response = client.post(
        "/ingest", 
        json={"event": "test"}, 
        headers={"X-API-Key": "wrong"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid API Key"}
