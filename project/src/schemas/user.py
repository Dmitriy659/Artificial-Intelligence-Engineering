import re
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class RegisterSchema(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=6, max_length=100)
    password: str = Field(..., min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"\d", v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Пароль должен содержать хотя бы один спецсимвол")
        return v


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class LoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str


class RefreshTokenResponseSchema(BaseModel):
    access_token: str


class UserSchema(BaseModel):
    id: UUID
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UpdateUserSchema(BaseModel):
    username: str = Field(..., min_length=6, max_length=100)
