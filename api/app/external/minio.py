import time
from pathlib import Path

from minio import Minio
from minio.error import S3Error
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MinioConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MINIO_",
        extra="ignore",
    )

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool
    retries: int = Field(ge=1)
    initial_delay: float = Field(gt=0)
    max_delay: float = Field(gt=0)


class MinioClient:
    def __init__(self, config: MinioConfig) -> None:
        self.config = config
        self._client = Minio(
            config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
        )

    def download_object(self, object_key: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        delay = self.config.initial_delay
        for attempt in range(1, self.config.retries + 1):
            try:
                if not self._client.bucket_exists(self.config.bucket):
                    raise RuntimeError(f"MinIO bucket '{self.config.bucket}' does not exist")
                self._client.fget_object(self.config.bucket, object_key, str(destination))
                return
            except S3Error as e:
                if e.code == "NoSuchKey":
                    raise RuntimeError(
                        f"Object '{object_key}' not found in bucket '{self.config.bucket}'"
                    ) from e
                elif e.code == "AccessDenied":
                    raise RuntimeError(f"Access denied to bucket '{self.config.bucket}'") from e
                elif e.code in {
                    "InternalError",
                    "ServiceUnavailable",
                    "SlowDown",
                    "RequestTimeout",
                    "Throttling",
                }:
                    if attempt == self.config.retries:
                        raise RuntimeError(
                            f"MinIO transient error after {self.config.retries} attempts: {e}"
                        ) from e
                    time.sleep(delay)
                    delay = min(delay * 2, self.config.max_delay)
                else:
                    raise RuntimeError(f"MinIO error: {e}") from e
            except Exception:
                if attempt == self.config.retries:
                    raise
                time.sleep(delay)
                delay = min(delay * 2, self.config.max_delay)
