from fastapi import APIRouter, status

from ..orm.orm_base import engine
from sqlalchemy import text
from fastapi.responses import JSONResponse

check_router = APIRouter(tags=["health"])


@check_router.get("/health")
async def health():
    return {
        "status": "ok"
    }


@check_router.get("/ready")
async def readiness():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "reason": "database_unavailable",
                "detail": str(e)
            }
        )

    return {
        "status": "ready"
    }
