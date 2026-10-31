import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.endpoints import auth, health, predict
from app.config import get_settings
from app.db.session import init_db
from app.external.minio import MinioClient, MinioConfig
from app.services.model_service import (
    InvalidInputShapeError,
    ModelInferenceError,
    ModelNotReadyError,
    ModelService,
)

logger = getLogger(__name__)


def get_minio_config() -> MinioConfig:
    return MinioConfig(
        endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        bucket=os.getenv("MINIO_BUCKET", "models"),
        secure=os.getenv("MINIO_SECURE", "true").lower() == "true",
        retries=max(1, int(os.getenv("MINIO_RETRIES", "10"))),
        initial_delay=float(os.getenv("MINIO_INITIAL_DELAY_SECONDS", "1.0")),
        max_delay=float(os.getenv("MINIO_MAX_DELAY_SECONDS", "30.0")),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    model_service = ModelService(
        model_path=settings.model_path,
        minio_client=MinioClient(get_minio_config()),
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(auth.router)
app.include_router(predict.router)
