from fastapi import APIRouter

from .v1 import v1_router
from .health import check_router

api_router = APIRouter(prefix="/api")
api_router.include_router(v1_router)

health_router = APIRouter()
health_router.include_router(check_router)
