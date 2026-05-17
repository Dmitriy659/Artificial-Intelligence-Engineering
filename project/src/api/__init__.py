from fastapi import APIRouter

from .health import check_router
from .v1 import v1_router

api_router = APIRouter(prefix="/api")
api_router.include_router(v1_router)

health_router = APIRouter()
health_router.include_router(check_router)
