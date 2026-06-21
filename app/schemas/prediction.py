from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "features": [2018, 45000, 1.6, 110, 5],
        }
    })

    features: list[float] = Field(
        min_length=1,
        description="Ordered numeric feature vector expected by the trained model.",
    )


class PredictionResponse(BaseModel):
    prediction: float | int | str | list[float | int | str]
    model_version: str
    request_id: str
