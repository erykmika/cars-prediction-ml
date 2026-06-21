from fastapi import APIRouter, Request

from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    model_service = request.app.state.model_service

    return HealthResponse(
        status="ok" if model_service.is_ready else "degraded",
        app_name=request.app.state.settings.app_name,
        environment=request.app.state.settings.environment,
        model_loaded=model_service.is_ready,
        model_path=str(model_service.model_path),
        detail=model_service.load_error,
    )
