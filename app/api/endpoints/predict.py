from fastapi import APIRouter, Request

from app.schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter(prefix="/predict", tags=["prediction"])


@router.post("", response_model=PredictionResponse)
async def predict(payload: PredictionRequest, request: Request) -> PredictionResponse:
    model_service = request.app.state.model_service
    mock_db = request.app.state.mock_db

    result = model_service.predict(payload.features)
    record = mock_db.save_prediction(features=payload.features, prediction=result)

    return PredictionResponse(
        prediction=result,
        model_version=model_service.model_version,
        request_id=record["request_id"],
    )
