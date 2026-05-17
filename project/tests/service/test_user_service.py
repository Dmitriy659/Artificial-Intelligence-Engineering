import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.orm.models import UserModel
from src.schemas.user import LoginSchema, RegisterSchema, UpdateUserSchema
from src.service.user_service import (
    get_user_by_id,
    login_user,
    refresh_access_token,
    register_user,
    update_user_service,
)


@pytest.mark.asyncio
async def test_register_user_success():
    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    uow.repository.add_user = AsyncMock()
    uow.commit = AsyncMock()

    data = RegisterSchema(
        email="test@example.com",
        username="tester123",
        password="StrongPass1!",
    )

    with patch("src.service.user_service.hash_password", return_value="hashed"):
        await register_user(data, uow)

    uow.repository.add_user.assert_awaited_once()
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_success():
    user = UserModel(
        id=uuid4(),
        email="test@example.com",
        username="tester",
        password_hash="hashed",
        created_at=datetime.datetime.now(),
    )

    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.repository.get_user_by_email = AsyncMock(return_value=user)
    uow.commit = AsyncMock()

    data = LoginSchema(email="test@example.com", password="StrongPass1!")

    with patch("src.service.user_service.verify_password", return_value=True), patch(
        "src.service.user_service.create_access_token", return_value="access"
    ), patch("src.service.user_service.create_refresh_token", return_value="refresh"):

        result = await login_user(data, uow)

    assert result.access_token == "access"
    assert result.refresh_token == "refresh"


@pytest.mark.asyncio
async def test_login_wrong_password():
    user = UserModel(
        id=uuid4(),
        email="test@example.com",
        username="tester",
        password_hash="hashed",
        created_at=datetime.datetime.now(),
    )

    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.repository.get_user_by_email = AsyncMock(return_value=user)
    uow.commit = AsyncMock()

    data = LoginSchema(email="test@example.com", password="wrong")

    with patch("src.service.user_service.verify_password", return_value=False):

        with pytest.raises(HTTPException) as exc:
            await login_user(data, uow)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_user_success():
    user = UserModel(
        id=uuid4(),
        email="test@example.com",
        username="tester",
        password_hash="hashed",
        created_at=datetime.datetime.now(),
    )

    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.repository.get_user_by_id = AsyncMock(return_value=user)
    uow.commit = AsyncMock()

    result = await get_user_by_id(user.id, uow)

    assert result.id == user.id
    assert result.email == user.email


@pytest.mark.asyncio
async def test_update_user():
    user = UserModel(
        id=uuid4(),
        email="test@example.com",
        username="old",
        password_hash="hash",
        created_at=datetime.datetime.now(),
    )

    updated = UserModel(
        id=user.id,
        email=user.email,
        username="newname",
        password_hash="hash",
        created_at=datetime.datetime.now(),
    )

    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    uow.repository.get_user_by_id = AsyncMock(return_value=user)
    uow.repository.update_user = AsyncMock(return_value=updated)
    uow.commit = AsyncMock()

    result = await update_user_service(
        user.id,
        UpdateUserSchema(username="newname"),
        uow,
    )

    assert result.username == "newname"


@pytest.mark.asyncio
async def test_refresh_token():
    with patch("src.service.user_service.decode_token") as decode_mock, patch(
        "src.service.user_service.create_access_token", return_value="new_access"
    ):

        decode_mock.return_value = {
            "sub": "user-123",
            "type": "refresh",
        }

        result = await refresh_access_token("refresh_token")

    assert result.access_token == "new_access"
