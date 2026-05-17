from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.api.auth import (
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.api.auth import get_current_user, create_access_token


def test_create_access_token():
    token = create_access_token("user-123")

    assert isinstance(token, str)

    payload = decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_create_refresh_token():
    token = create_refresh_token("user-123")

    payload = decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["type"] == "refresh"


def test_decode_token_invalid():
    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        decode_token("invalid.token.value")

    assert exc.value.status_code == 401
    assert "Invalid or expired token" in exc.value.detail


def test_hash_and_verify_password():
    password = "StrongPass1!"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpass", hashed) is False


@pytest.mark.asyncio
async def test_get_current_user_success():
    token = create_access_token("user-123")

    credentials = MagicMock()
    credentials.credentials = token

    user = await get_current_user(credentials)

    assert user["sub"] == "user-123"
    assert user["type"] == "access"


@pytest.mark.asyncio
async def test_get_current_user_wrong_type():
    from src.api.auth import create_refresh_token

    token = create_refresh_token("user-123")

    credentials = MagicMock()
    credentials.credentials = token

    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials)

    assert exc.value.status_code == 401
    assert "Invalid token type" in exc.value.detail
