from pydantic import BaseModel, ConfigDict, Field, field_validator

type FeatureValue = str | float | int | bool | None
type PredictionValue = float | int | str | list[float | int | str]


class PredictionResponse(BaseModel):
    prediction: PredictionValue


class PredictionRequest(BaseModel):  # TODO add validation
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "features": {
                    "brand": "Toyota",
                    "model": "Corolla",
                    "year": 2018,
                    "mileage": 45000,
                    "fuel": "Petrol",
                    "transmission": "Manual",
                    "engine_capacity": 1.6,
                    "power": 110,
                },
            }
        }
    )

    features: dict[str, FeatureValue] | list[float] = Field(
        description=(
            "Feature mapping expected by the trained preprocessing pipeline. "
            "A numeric vector is also accepted for simple legacy estimators."
        ),
    )

    @field_validator("features")
    @classmethod
    def features_must_not_be_empty(
        cls,
        value: dict[str, FeatureValue] | list[float],
    ) -> dict[str, FeatureValue] | list[float]:
        if len(value) == 0:
            raise ValueError("features must not be empty")
        return value
