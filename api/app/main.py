from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.endpoints import health, predict
from app.core.config import get_settings
from app.db.session import init_db
from app.services.model_service import (
    InvalidInputShapeError,
    ModelInferenceError,
    ModelNotReadyError,
    ModelService,
)

logger = getLogger(__name__)


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
    init_db()

    yield


app = FastAPI(
    title="Cars Prediction ML API",
    version="0.1.0",
    lifespan=lifespan,
)

logger.info("Starting Cars Prediction ML API...")

settings = get_settings()

logger.info(f"Model path: {settings.model_path}")
logger.info(f"Model version: {settings.model_version}")
logger.info(f"Database URL: {settings.database_url[:5] if settings.database_url else 'Not set'}***")


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
