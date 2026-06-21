from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_degraded_without_model_file() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["model_loaded"] is False
    assert "Model file not found" in payload["detail"]
