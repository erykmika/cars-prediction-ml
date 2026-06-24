from collections.abc import Mapping
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.schemas.prediction import FeatureValue


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
        self.feature_columns: list[str] | None = None
        self.target_column: str | None = None
        self.metrics: dict[str, Any] = {}
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
            loaded_artifact = joblib.load(resolved_path)
            self._apply_loaded_artifact(loaded_artifact)
            self.load_error = None
        except Exception as exc:
            self.model = None
            self.load_error = f"Failed to load model: {exc}"

    def predict(
        self,
        features: Mapping[str, FeatureValue] | list[float],
    ) -> float | int | str | list[float | int | str]:
        if not self.is_ready:
            detail = self.load_error or "Model has not been loaded."
            raise ModelNotReadyError(detail)

        model_input = self._build_model_input(features)

        try:
            raw_prediction = self.model.predict(model_input)
        except ValueError as exc:
            raise InvalidInputShapeError(f"Invalid input shape: {exc}") from exc
        except Exception as exc:
            raise ModelInferenceError(f"Model inference failed: {exc}") from exc

        return self._serialize_prediction(raw_prediction)

    def _apply_loaded_artifact(self, loaded_artifact: Any) -> None:
        if isinstance(loaded_artifact, dict) and "model" in loaded_artifact:
            self.model = loaded_artifact["model"]
            self.feature_columns = loaded_artifact.get("feature_columns")
            self.target_column = loaded_artifact.get("target_column")
            self.metrics = loaded_artifact.get("metrics", {})
            self.model_version = loaded_artifact.get("model_version", self.model_version)
            return

        self.model = loaded_artifact
        self.feature_columns = None
        self.target_column = None
        self.metrics = {}

    def _build_model_input(
        self,
        features: Mapping[str, FeatureValue] | list[float],
    ) -> pd.DataFrame | np.ndarray:
        if isinstance(features, Mapping):
            return self._to_feature_frame(features)

        if self.feature_columns is not None:
            if len(features) != len(self.feature_columns):
                raise InvalidInputShapeError(
                    f"Expected {len(self.feature_columns)} features, received {len(features)}."
                )
            return pd.DataFrame([features], columns=self.feature_columns)

        feature_array = self._to_feature_array(features)
        expected_features = getattr(self.model, "n_features_in_", None)

        if expected_features is not None and feature_array.shape[1] != expected_features:
            raise InvalidInputShapeError(
                f"Expected {expected_features} features, received {feature_array.shape[1]}."
            )

        return feature_array

    def _to_feature_frame(self, features: Mapping[str, FeatureValue]) -> pd.DataFrame:
        if not self.feature_columns:
            return pd.DataFrame([dict(features)])

        missing_features = sorted(set(self.feature_columns) - set(features))
        extra_features = sorted(set(features) - set(self.feature_columns))

        if missing_features:
            raise InvalidInputShapeError(
                "Missing required feature columns: " + ", ".join(missing_features)
            )

        if extra_features:
            raise InvalidInputShapeError(
                "Received unknown feature columns: " + ", ".join(extra_features)
            )

        return pd.DataFrame([{column: features[column] for column in self.feature_columns}])

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
