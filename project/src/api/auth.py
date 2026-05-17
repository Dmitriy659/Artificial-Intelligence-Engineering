import datetime
import hashlib
from typing import TypedDict

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.settings.settings import SecuritySettings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class PayloadRefresh(TypedDict):
    sub: str
    exp: datetime.datetime
    type: str


class PayloadAccess(PayloadRefresh):
    role: str


def create_access_token(user_id: str) -> str:
    settings = SecuritySettings()

    payload = {
        "sub": user_id,
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30),  # TODO только для разработки
        "type": "access",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def create_refresh_token(user_id: str) -> str:
    settings = SecuritySettings()

    payload = {
        "sub": user_id,
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30),
        "type": "refresh",
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> PayloadAccess | PayloadRefresh:
    settings = SecuritySettings()

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(401, "Invalid token type")

    return payload


def hash_password(password: str) -> str:
    password = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password = hashlib.sha256(plain_password.encode()).hexdigest()
    return pwd_context.verify(plain_password, hashed_password)


async def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return credentials.credentials
