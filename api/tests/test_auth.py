from unittest.mock import Mock

import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.endpoints.auth import require_logged_in
from app.db.models import User
from app.main import app
from app.services.auth_service import AuthService


def test_health_endpoint_public() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["model_loaded"] is False


def test_login_success(auth_headers, test_user) -> None:
    with TestClient(app) as client:
        response = client.post("/auth/login", json={"username": "testuser", "password": "testpass"})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/auth/login", json={"username": "testuser", "password": "wrongpass"}
        )

    assert response.status_code == 401


def test_login_nonexistent_user() -> None:
    with TestClient(app) as client:
        response = client.post("/auth/login", json={"username": "nonexistent", "password": "pass"})

    assert response.status_code == 401


def test_refresh_token(auth_headers, test_user) -> None:
    with TestClient(app) as client:
        # First login to get refresh token
        login_response = client.post(
            "/auth/login", json={"username": "testuser", "password": "testpass"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_invalid_token() -> None:
    with TestClient(app) as client:
        response = client.post("/auth/refresh", json={"refresh_token": "invalid-token"})

    assert response.status_code == 401


def test_get_me(auth_headers, test_user) -> None:
    with TestClient(app) as client:
        response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["is_active"] is True


def test_get_me_without_auth() -> None:
    with TestClient(app) as client:
        response = client.get("/auth/me")

    assert response.status_code == 401


def test_is_logged_in_accepts_only_valid_access_tokens() -> None:
    auth_service = AuthService()
    access_token, refresh_token = auth_service.create_login_tokens("testuser")

    assert auth_service.is_logged_in(access_token) is True
    assert auth_service.is_logged_in(refresh_token) is False
    assert auth_service.is_logged_in("invalid-token") is False


def test_require_logged_in_does_not_look_up_user(monkeypatch) -> None:
    auth_service = AuthService()
    access_token = auth_service.create_login_tokens("testuser")[0]
    user_lookup = Mock(side_effect=AssertionError("User lookup should not be called"))
    query = Mock(side_effect=AssertionError("Database query should not be called"))
    select = Mock(side_effect=AssertionError("SQL select should not be called"))
    monkeypatch.setattr(auth_service, "get_current_user", user_lookup)
    monkeypatch.setattr(Session, "query", query)
    monkeypatch.setattr(sqlalchemy, "select", select)

    require_logged_in(token=access_token, auth_service=auth_service)

    user_lookup.assert_not_called()
    assert not any(User in call.args for call in query.call_args_list)
    assert not any(User in call.args for call in select.call_args_list)
