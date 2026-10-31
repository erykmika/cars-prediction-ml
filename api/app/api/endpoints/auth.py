from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.schemas.auth import LoginRequest, Token, UserResponse
from app.db.models import User
from app.db.session import get_db
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    user = auth_service.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/login", response_model=Token)
async def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    response: Response,
) -> Token:
    user = auth_service.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token = auth_service.create_login_tokens(user.username)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return Token(access_token=access_token, refresh_token="")


@router.post("/refresh", response_model=Token)
async def refresh_token(
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Token:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tokens = auth_service.refresh_tokens(db, refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    new_access, new_refresh = tokens
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return Token(access_token=new_access, refresh_token="")


@router.post("/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie(key="refresh_token", httponly=True, secure=False, samesite="lax")
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )
