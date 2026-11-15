from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.schemas.auth import TokenPayload
from app.config import get_settings
from app.db.models import User


class AuthService:
    def __init__(self):
        self._pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        self._settings = get_settings()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self._pwd_context.verify(plain_password, hashed_password)

    def _get_password_hash(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def _create_access_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=self._settings.access_token_expire_minutes
            )
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode, self._settings.jwt_secret_key, algorithm=self._settings.jwt_algorithm
        )
        return encoded_jwt

    def _create_refresh_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(days=self._settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, self._settings.jwt_secret_key, algorithm=self._settings.jwt_algorithm
        )
        return encoded_jwt

    def _decode_token(self, token: str) -> TokenPayload | None:
        try:
            payload = jwt.decode(
                token, self._settings.jwt_secret_key, algorithms=[self._settings.jwt_algorithm]
            )
            return TokenPayload.model_validate(payload)
        except JWTError, ValidationError:
            return None

    def _create_token_pair(self, username: str) -> tuple[str, str]:
        access_token = self._create_access_token({"sub": username})
        refresh_token = self._create_refresh_token({"sub": username})
        return access_token, refresh_token

    def authenticate_user(self, db: Session, username: str, password: str) -> User | None:
        user = db.query(User).filter(User.username == username).first()
        if not user or not self._verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def get_current_user(self, db: Session, token: str) -> User | None:
        token_data = self._decode_token(token)
        if not token_data or token_data.type != "access":
            return None
        user = db.query(User).filter(User.username == token_data.sub).first()
        if user is None or not user.is_active:
            return None
        return user

    def is_logged_in(self, token: str) -> bool:
        token_data = self._decode_token(token)
        return token_data is not None and token_data.type == "access"

    def refresh_tokens(self, db: Session, refresh_token: str) -> tuple[str, str] | None:
        token_data = self._decode_token(refresh_token)
        if not token_data or token_data.type != "refresh":
            return None
        user = db.query(User).filter(User.username == token_data.sub).first()
        if not user or not user.is_active:
            return None
        return self._create_token_pair(user.username)

    def create_login_tokens(self, username: str) -> tuple[str, str]:
        return self._create_token_pair(username)


def get_auth_service() -> AuthService:
    return AuthService()
