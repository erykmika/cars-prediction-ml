from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.endpoints import health, predict
from app.core.config import get_settings
from app.services.mock_db import MockPredictionRepository
from app.services.model_service import (
    InvalidInputShapeError,
    ModelInferenceError,
    ModelNotReadyError,
    ModelService,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    model_service = ModelService(
        model_path=settings.model_path,
        model_version=settings.model_version,
    )
    model_service.load_model()

    app.state.settings = settings
    app.state.model_service = model_service
    app.state.mock_db = MockPredictionRepository()

    yield


app = FastAPI(
    title="Cars Prediction ML API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(ModelNotReadyError)
async def model_not_ready_handler(
    request: Request,
    exc: ModelNotReadyError,
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(InvalidInputShapeError)
async def invalid_input_shape_handler(
    request: Request,
    exc: InvalidInputShapeError,
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(ModelInferenceError)
async def model_inference_handler(
    request: Request,
    exc: ModelInferenceError,
) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


app.include_router(health.router)
app.include_router(predict.router)
