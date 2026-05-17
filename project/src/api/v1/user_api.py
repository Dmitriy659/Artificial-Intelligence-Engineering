from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.adapters import unit_work
from src.api.auth import get_current_user
from src.schemas.user import (
    LoginResponseSchema,
    LoginSchema,
    RefreshTokenResponseSchema,
    RegisterSchema,
    UpdateUserSchema,
    UserSchema,
)
from src.service.user_service import (
    get_user_by_id,
    login_user,
    refresh_access_token,
    register_user,
    update_user_service,
)

user_router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()


@user_router.post("/register")
async def register(data: RegisterSchema):
    await register_user(data, unit_work.SqlAlchemyUnitOfWork())
    return {"message": "User created"}


@user_router.post("/login", response_model=LoginResponseSchema)
async def login(data: LoginSchema):
    return await login_user(data, unit_work.SqlAlchemyUnitOfWork())


@user_router.post("/refresh", response_model=RefreshTokenResponseSchema)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    return await refresh_access_token(credentials.credentials)


@user_router.put("/me", response_model=UserSchema)
async def update_user(
    data: UpdateUserSchema,
    user: dict = Depends(get_current_user),
):
    return await update_user_service(user["sub"], data, unit_work.SqlAlchemyUnitOfWork())


@user_router.get("/me", response_model=UserSchema)
async def get_user(
    user: dict = Depends(get_current_user),
):
    print(user["sub"])
    return await get_user_by_id(user["sub"], unit_work.SqlAlchemyUnitOfWork())
