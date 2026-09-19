from pathlib import Path

from app.services.model_service import ModelService


def create_model_service(model_path: Path) -> ModelService:
    return ModelService(model_path=model_path, minio_client=None)  # type: ignore[arg-type]


def test_load_model_sets_error_when_joblib_cannot_deserialize_file(tmp_path, monkeypatch) -> None:
    model_path = tmp_path / "corrupt-model.joblib"
    model_path.write_bytes(b"not a joblib artifact")

    def raise_deserialization_error(path):
        raise ValueError("invalid load key")

    monkeypatch.setattr("app.services.model_service.joblib.load", raise_deserialization_error)
    service = create_model_service(model_path)

    service.load_model()

    assert not service.is_ready
    assert service.load_error == (f"Failed to load model from '{model_path}': invalid load key")


def test_load_model_sets_error_when_artifact_application_fails(tmp_path, monkeypatch) -> None:
    model_path = tmp_path / "model.joblib"
    model_path.write_bytes(b"serialized artifact")
    monkeypatch.setattr("app.services.model_service.joblib.load", lambda path: object())

    service = create_model_service(model_path)

    def raise_artifact_error(loaded_artifact):
        raise TypeError("missing model metadata")

    monkeypatch.setattr(service, "_apply_loaded_artifact", raise_artifact_error)

    service.load_model()

    assert not service.is_ready
    assert service.load_error == f"Invalid model artifact at '{model_path}': missing model metadata"
