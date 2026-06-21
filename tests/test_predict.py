from fastapi.testclient import TestClient

from app.main import app


class DummyModel:
    n_features_in_ = 2

    def predict(self, rows):
        return [rows[0][0] + rows[0][1]]


def test_predict_returns_prediction_with_loaded_model() -> None:
    with TestClient(app) as client:
        app.state.model_service.model = DummyModel()
        app.state.model_service.load_error = None

        response = client.post("/predict", json={"features": [10, 15]})

    assert response.status_code == 200
    payload = response.json()
    assert payload["prediction"] == 25
    assert payload["model_version"] == "unknown"
    assert payload["request_id"]


def test_predict_rejects_invalid_feature_count() -> None:
    with TestClient(app) as client:
        app.state.model_service.model = DummyModel()
        app.state.model_service.load_error = None

        response = client.post("/predict", json={"features": [10]})

    assert response.status_code == 422
    assert response.json()["detail"] == "Expected 2 features, received 1."


def test_predict_returns_503_when_model_is_missing() -> None:
    with TestClient(app) as client:
        response = client.post("/predict", json={"features": [10, 15]})

    assert response.status_code == 503
    assert "Model file not found" in response.json()["detail"]
