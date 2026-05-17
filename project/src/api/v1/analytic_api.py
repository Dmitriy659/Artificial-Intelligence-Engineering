from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ...adapters import unit_work
from ...adapters.s3_client import S3Client
from ...schemas.analytic import AnalyticFullResponseSchema, AnalyticResponseSchema
from ...service.analytic_service import (
    analyze_analytic_service,
    create_analytic_service,
    delete_analytic_service,
    get_analytic_service,
    get_analytic_service_full,
    list_analytics_service,
)
from ...settings.settings import S3Settings
from ..auth import get_current_user

analytic_router = APIRouter(prefix="/analytic", tags=["analytic"])


@analytic_router.post("/", response_model=AnalyticResponseSchema)
async def create_analytic(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="File must be .csv or .xlsx")

    s3_client: S3Client = S3Client(S3Settings())
    user_id = user["sub"]
    return await create_analytic_service(
        user_id,
        file,
        s3_client,
        unit_work.SqlAlchemyUnitOfWork(),
    )


@analytic_router.post("/{analytic_id}/analyze", response_model=AnalyticResponseSchema)
async def analyze_analytic(analytic_id: UUID, user=Depends(get_current_user)):
    s3_client: S3Client = S3Client(S3Settings())
    user_id = user["sub"]

    return await analyze_analytic_service(
        analytic_id,
        user_id,
        s3_client,
        unit_work.SqlAlchemyUnitOfWork(),
    )


@analytic_router.get("/", response_model=list[AnalyticResponseSchema])
async def list_analytics(user=Depends(get_current_user)):
    user_id = user["sub"]

    return await list_analytics_service(user_id, unit_work.SqlAlchemyUnitOfWork())


@analytic_router.get("/{analytic_id}/full", response_model=AnalyticFullResponseSchema)
async def get_analytic_full(analytic_id: UUID, user=Depends(get_current_user)):
    user_id = user["sub"]

    return await get_analytic_service_full(
        analytic_id,
        user_id,
        unit_work.SqlAlchemyUnitOfWork(),
    )


@analytic_router.get("/{analytic_id}", response_model=AnalyticResponseSchema)
async def get_analytic(analytic_id: UUID, user=Depends(get_current_user)):
    user_id = user["sub"]

    return await get_analytic_service(
        analytic_id,
        user_id,
        unit_work.SqlAlchemyUnitOfWork(),
    )


@analytic_router.delete("/{analytic_id}")
async def delete_analytic(analytic_id: UUID, user=Depends(get_current_user)):
    s3_client: S3Client = S3Client(S3Settings())
    user_id = user["sub"]

    return await delete_analytic_service(
        analytic_id,
        user_id,
        s3_client,
        unit_work.SqlAlchemyUnitOfWork(),
    )
