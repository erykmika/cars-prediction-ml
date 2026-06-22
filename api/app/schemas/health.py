from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    model_loaded: bool
    model_path: str
    detail: str | None = None
