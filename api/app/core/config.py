from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "cars-prediction-api"
    environment: str = "local"
    log_level: str = "INFO"
    model_path: Path = Field(default=Path("models/poland_used_cars_linear_regression.joblib"))
    model_version: str = "unknown"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/cars_predictions"

    # JWT Settings
    jwt_secret_key: str = "change-me-in-production-use-strong-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
