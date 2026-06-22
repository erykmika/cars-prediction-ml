from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.schemas.prediction import FeatureValue


class MockPredictionRepository: # TODO: use
    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def save_prediction(
        self,
        *,
        features: dict[str, FeatureValue] | list[float],
        prediction: float | int | str | list[float | int | str],
    ) -> dict[str, Any]:
        record = {
            "request_id": str(uuid4()),
            "features": features,
            "prediction": prediction,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._records.append(record)
        return record

    def list_predictions(self) -> list[dict[str, Any]]:
        return self._records.copy()
