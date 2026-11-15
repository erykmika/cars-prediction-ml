from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.endpoints.auth import require_logged_in
from app.api.schemas.prediction import PredictionRequest, PredictionResponse
from app.db.repository import PredictionRepository
from app.db.session import get_db

router = APIRouter(
    prefix="/predict",
    tags=["prediction"],
    dependencies=[Depends(require_logged_in)],
)


@router.post("", response_model=PredictionResponse)
async def predict(
    payload: PredictionRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> PredictionResponse:
    model_service = request.app.state.model_service
    repo = PredictionRepository(db)

    result = model_service.predict(payload.features)
    address = request.client.host if request.client else "unknown"
    repo.save_prediction(address=address, features=payload.features, prediction=result)

    return PredictionResponse(prediction=result)
