import os
import time
from dataclasses import dataclass
from pathlib import Path

from minio import Minio
from minio.error import S3Error


@dataclass
class MinioConfig:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool
    retries: int
    initial_delay: float
    max_delay: float


DEFAULT_MINIO_RETRIES = 10
DEFAULT_MINIO_INITIAL_DELAY_SECONDS = 1.0
DEFAULT_MINIO_MAX_DELAY_SECONDS = 30.0


class MinioClient:
    def __init__(self, config: MinioConfig | None = None) -> None:
        if config is None:
            config = self._get_default_config()
        self.config = config
        self._client = Minio(
            config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
        )

    @staticmethod
    def _get_default_config() -> MinioConfig:
        return MinioConfig(
            endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            bucket=os.getenv("MINIO_BUCKET", "models"),
            secure=os.getenv("MINIO_SECURE", "true").lower() == "true",
            retries=max(1, int(os.getenv("MINIO_RETRIES", str(DEFAULT_MINIO_RETRIES)))),
            initial_delay=float(
                os.getenv("MINIO_INITIAL_DELAY_SECONDS", str(DEFAULT_MINIO_INITIAL_DELAY_SECONDS))
            ),
            max_delay=float(
                os.getenv("MINIO_MAX_DELAY_SECONDS", str(DEFAULT_MINIO_MAX_DELAY_SECONDS))
            ),
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