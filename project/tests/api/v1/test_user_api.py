from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.api.v1.user_api import user_router


@patch("src.api.v1.user_api.register_user", new_callable=AsyncMock)
@patch("src.api.v1.user_api.unit_work.SqlAlchemyUnitOfWork")
def test_register_success(mock_uow, mock_service, client_factory):
    client = client_factory([user_router])
    response = client.post(
        "/users/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "StrongPass1!",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User created"

    mock_service.assert_awaited_once()


def test_register_password_validation(client_factory):
    client = client_factory([user_router])
    response = client.post(
        "/users/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak",
        },
    )

    assert response.status_code == 422


@patch("src.api.v1.user_api.login_user", new_callable=AsyncMock)
@patch("src.api.v1.user_api.unit_work.SqlAlchemyUnitOfWork")
def test_login_success(mock_uow, mock_service, client_factory):
    client = client_factory([user_router])
    mock_service.return_value = {
        "access_token": "access123",
        "refresh_token": "refresh123",
    }

    response = client.post(
        "/users/login",
        json={
            "email": "test@example.com",
            "password": "StrongPass1!",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()

    mock_service.assert_awaited_once()


@patch("src.api.v1.user_api.refresh_access_token", new_callable=AsyncMock)
def test_refresh_token_success(mock_service, client_factory):
    client = client_factory([user_router])
    mock_service.return_value = {
        "access_token": "new_access_token",
    }

    response = client.post(
        "/users/refresh",
        headers={"Authorization": "Bearer old_token"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "new_access_token"

    mock_service.assert_awaited_once_with("old_token")


@patch("src.api.v1.user_api.update_user_service", new_callable=AsyncMock)
@patch("src.api.v1.user_api.unit_work.SqlAlchemyUnitOfWork")
def test_update_user_success(mock_uow, mock_service, client_factory):
    client = client_factory([user_router])
    mock_service.return_value = {
        "id": str(uuid4()),
        "username": "updateduser",
        "email": "test@example.com",
    }

    response = client.put(
        "/users/me",
        json={"username": "updateduser"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "updateduser"

    mock_service.assert_awaited_once()


@patch("src.api.v1.user_api.get_user_by_id", new_callable=AsyncMock)
@patch("src.api.v1.user_api.unit_work.SqlAlchemyUnitOfWork")
def test_get_user_success(mock_uow, mock_service, client_factory):
    client = client_factory([user_router])
    mock_service.return_value = {
        "id": str(uuid4()),
        "username": "testuser",
        "email": "test@example.com",
    }

    response = client.get("/users/me")

    assert response.status_code == 200
    assert "username" in response.json()

    mock_service.assert_awaited_once()
