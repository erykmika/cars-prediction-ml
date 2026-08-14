from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Prediction


class PredictionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save_prediction(
        self,
        *,
        address: str,
        features: dict[str, Any] | list[float],
        prediction: Any,
    ) -> dict[str, Any]:
        record = Prediction(
            client_address=address,
            features=features,
            prediction=float(prediction),
            created_at=datetime.now(UTC),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return {
            "client_address": record.client_address,
            "features": record.features,
            "prediction": record.prediction,
            "created_at": record.created_at.isoformat(),
        }

    def list_predictions(self) -> list[dict[str, Any]]:
        records = self.db.query(Prediction).order_by(Prediction.created_at.desc()).all()
        return [
            {
                "client_address": r.client_address,
                "features": r.features,
                "prediction": r.prediction,
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ]
