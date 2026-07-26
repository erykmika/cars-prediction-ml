from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.repository import PredictionRepository
from app.db.session import get_db
from app.schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter(prefix="/predict", tags=["prediction"])


@router.post("", response_model=PredictionResponse)
async def predict(
    payload: PredictionRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> PredictionResponse:
    model_service = request.app.state.model_service
    repo = PredictionRepository(db)

    result = model_service.predict(payload.features)
    record = repo.save_prediction(features=payload.features, prediction=result)

    return PredictionResponse(
        prediction=result,
        model_version=model_service.model_version,
        request_id=record["request_id"],
    )
