from fastapi.testclient import TestClient

from app.db.models import Prediction
from app.main import app
from tests.conftest import TestingSessionLocal


class DummyModel:
    n_features_in_ = 2

    def predict(self, rows):
        return [rows[0][0] + rows[0][1]]


class DummyFrameModel:
    def predict(self, rows):
        return [rows.iloc[0]["year"] - rows.iloc[0]["mileage"]]


def test_predict_returns_prediction_with_loaded_model() -> None:
    with TestClient(app) as client:
        app.state.model_service.model = DummyModel()
        app.state.model_service.load_error = None

        response = client.post("/predict", json={"features": [10, 15]})

    assert response.status_code == 200
    assert response.json() == {"prediction": 25}


def test_predict_accepts_trained_model_feature_mapping() -> None:
    with TestClient(app) as client:
        app.state.model_service.model = DummyFrameModel()
        app.state.model_service.feature_columns = ["year", "mileage"]
        app.state.model_service.load_error = None

        response = client.post("/predict", json={"features": {"year": 2020, "mileage": 500}})

    assert response.status_code == 200
    assert response.json() == {"prediction": 1520}


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


def test_predict_persists_client_address() -> None:
    with TestClient(app) as client:
        app.state.model_service.model = DummyModel()
        app.state.model_service.load_error = None

        response = client.post("/predict", json={"features": [10, 15]})

    assert response.status_code == 200
    with TestingSessionLocal() as db:
        records = db.query(Prediction).all()
        assert len(records) == 1
        assert records[0].client_address == "testclient"
        assert not hasattr(records[0], "request_id")
