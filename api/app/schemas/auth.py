from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "CARS_PREDICTION_USER",
                "password": "123",
            }
        }
    )

    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)
