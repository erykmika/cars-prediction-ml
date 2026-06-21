from pathlib import Path
from typing import Any

import joblib
import numpy as np


class ModelNotReadyError(RuntimeError):
    pass


class InvalidInputShapeError(ValueError):
    pass


class ModelInferenceError(RuntimeError):
    pass


class ModelService:
    def __init__(self, *, model_path: Path, model_version: str = "unknown") -> None:
        self.model_path = model_path
        self.model_version = model_version
        self.model: Any | None = None
        self.load_error: str | None = None

    @property
    def is_ready(self) -> bool:
        return self.model is not None and self.load_error is None

    def load_model(self) -> None:
        resolved_path = self.model_path.expanduser()

        if resolved_path.suffix.lower() not in {".joblib", ".pkl"}:
            self.load_error = (
                f"Unsupported model file extension '{resolved_path.suffix}'. "
                "Expected .joblib or .pkl."
            )
            return

        if not resolved_path.exists():
            self.load_error = f"Model file not found at '{resolved_path}'."
            return

        try:
            self.model = joblib.load(resolved_path)
            self.load_error = None
        except Exception as exc:
            self.model = None
            self.load_error = f"Failed to load model: {exc}"

    def predict(self, features: list[float]) -> float | int | str | list[float | int | str]:
        if not self.is_ready:
            detail = self.load_error or "Model has not been loaded."
            raise ModelNotReadyError(detail)

        feature_array = self._to_feature_array(features)
        expected_features = getattr(self.model, "n_features_in_", None)

        if expected_features is not None and feature_array.shape[1] != expected_features:
            raise InvalidInputShapeError(
                f"Expected {expected_features} features, received {feature_array.shape[1]}."
            )

        try:
            raw_prediction = self.model.predict(feature_array)
        except ValueError as exc:
            raise InvalidInputShapeError(f"Invalid input shape: {exc}") from exc
        except Exception as exc:
            raise ModelInferenceError(f"Model inference failed: {exc}") from exc

        return self._serialize_prediction(raw_prediction)

    def _to_feature_array(self, features: list[float]) -> np.ndarray:
        try:
            feature_array = np.asarray(features, dtype=float).reshape(1, -1)
        except ValueError as exc:
            raise InvalidInputShapeError(f"Features must be numeric: {exc}") from exc

        if feature_array.ndim != 2 or feature_array.shape[0] != 1:
            raise InvalidInputShapeError("Features must be a single one-dimensional vector.")

        return feature_array

    def _serialize_prediction(
        self,
        raw_prediction: Any,
    ) -> float | int | str | list[float | int | str]:
        values = np.asarray(raw_prediction).tolist()

        if isinstance(values, list) and len(values) == 1:
            values = values[0]

        if isinstance(values, list):
            return [self._serialize_scalar(value) for value in values]

        return self._serialize_scalar(values)

    def _serialize_scalar(self, value: Any) -> float | int | str:
        if isinstance(value, np.generic):
            value = value.item()

        if isinstance(value, bool):
            return int(value)

        if isinstance(value, int | float | str):
            return value

        return str(value)
