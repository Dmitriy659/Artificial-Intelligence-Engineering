from fastapi import APIRouter

from .analytic_api import analytic_router
from .predict_api import predict_router
from .user_api import user_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(analytic_router)
v1_router.include_router(user_router)
v1_router.include_router(predict_router)
