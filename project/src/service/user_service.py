from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from src.adapters.unit_work import AbstractUnitOfWork
from src.orm.models import UserModel

from ..api.auth import (
    PayloadAccess,
    PayloadRefresh,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from ..logger.get_logger import get_logger
from ..schemas.user import (
    LoginResponseSchema,
    LoginSchema,
    RefreshTokenResponseSchema,
    RegisterSchema,
    UpdateUserSchema,
    UserSchema,
)

logger = get_logger(__name__)


async def register_user(user_data: RegisterSchema, uow: AbstractUnitOfWork):
    user_orm: UserModel = UserModel(
        id=uuid4(),
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password),
    )

    async with uow:
        try:
            await uow.repository.add_user(user_orm)
            await uow.commit()
        except IntegrityError:
            raise HTTPException(status_code=400, detail="User already exists")


async def login_user(user_data: LoginSchema, uow: AbstractUnitOfWork) -> LoginResponseSchema:
    async with uow:
        user_orm: UserModel | None = await uow.repository.get_user_by_email(str(user_data.email))

        if not user_orm:
            raise HTTPException(404, "User not found")
        await uow.commit()

    if not verify_password(user_data.password, user_orm.password_hash):
        raise HTTPException(401, "Invalid credentials")

    access_token = create_access_token(str(user_orm.id))
    refresh_token = create_refresh_token(str(user_orm.id))

    return LoginResponseSchema(access_token=access_token, refresh_token=refresh_token)


async def get_user_by_id(user_id: UUID, uow: AbstractUnitOfWork) -> UserSchema:
    async with uow:
        user_orm: UserModel | None = await uow.repository.get_user_by_id(user_id)
        if not user_orm:
            raise HTTPException(404, "User not found")
        await uow.commit()

    return UserSchema.model_validate(user_orm)


async def update_user_service(user_id: UUID, user_data: UpdateUserSchema, uow: AbstractUnitOfWork) -> UserSchema:
    async with uow:
        user_orm: UserModel | None = await uow.repository.get_user_by_id(user_id)
        if not user_orm:
            raise HTTPException(404, "User not found")
        user_orm.username = user_data.username

        user_orm: UserModel = await uow.repository.update_user(user_orm)
        await uow.commit()

    return UserSchema.model_validate(user_orm)


async def refresh_access_token(refresh_token: str) -> RefreshTokenResponseSchema:
    payload: PayloadAccess | PayloadRefresh = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type")

    user_id = str(payload["sub"])
    new_access_token: str = create_access_token(user_id)

    return RefreshTokenResponseSchema(access_token=new_access_token)
