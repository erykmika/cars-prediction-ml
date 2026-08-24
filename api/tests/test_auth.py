from fastapi.testclient import TestClient

from app.main import app


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
