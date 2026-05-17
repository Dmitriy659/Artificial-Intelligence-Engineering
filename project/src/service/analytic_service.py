import os
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile

from ..adapters.s3_client import S3Client
from ..adapters.unit_work import AbstractUnitOfWork
from ..exceptions import ModelNotFound
from ..logger.get_logger import get_logger
from ..orm.enums import AnalyticStatus
from ..orm.models import AnalyticModel
from ..schemas.analytic import AnalyticFullResponseSchema, AnalyticResponseSchema
from ..tasks.analytic.analyze import analyze_dataset

logger = get_logger(__name__)


async def create_analytic_service(
    user_id: UUID,
    file: UploadFile,
    s3_client: S3Client,
    uow: AbstractUnitOfWork,
) -> AnalyticResponseSchema:
    user_id = UUID(str(user_id))
    filename, extension = os.path.splitext(file.filename)

    async with uow:
        s3_key: str = f"analytic_{filename}_{uuid4()}{extension}"
        await s3_client.upload_file(file, s3_key)

        analytic_orm = AnalyticModel(
            id=uuid4(),
            user_id=user_id,
            status=AnalyticStatus.PENDING,
            dataset_name=file.filename,
            dataset_s3_key=s3_key,
        )
        created_analytic_orm: AnalyticModel = await uow.repository.create(analytic_orm)
        await uow.commit()

    return AnalyticResponseSchema.model_validate(created_analytic_orm)


async def analyze_analytic_service(
    analytic_id: UUID,
    user_id: UUID,
    s3_client: S3Client,
    uow: AbstractUnitOfWork,
) -> AnalyticResponseSchema:
    analytic_id = UUID(str(analytic_id))
    user_id = UUID(str(user_id))

    async with uow:
        analytic_orm: AnalyticModel | None = await uow.repository.get_analytic_by_id(analytic_id, user_id)
        if not analytic_orm:
            raise HTTPException(404, detail="Analytic not found")
        if analytic_orm.status != AnalyticStatus.PENDING:
            raise HTTPException(400, detail="Dataset not pending")

    try:
        await analyze_dataset(analytic_id, s3_client, uow)
    except ModelNotFound:
        raise HTTPException(404, detail="Analytic not found")

    async with uow:
        analytic_orm = await uow.repository.get_analytic_by_id(analytic_id, user_id)
        if not analytic_orm:
            raise HTTPException(404, detail="Analytic not found")

        return AnalyticResponseSchema.model_validate(analytic_orm)


async def get_analytic_service_full(
    analytic_id: UUID,
    user_id: UUID,
    uow: AbstractUnitOfWork,
) -> AnalyticFullResponseSchema:
    analytic_id = UUID(str(analytic_id))
    user_id = UUID(str(user_id))

    async with uow:
        analytic_orm: AnalyticModel | None = await uow.repository.get_analytic_full(analytic_id, user_id)
        if not analytic_orm:
            raise HTTPException(404, detail="Analytic not found")

        return AnalyticFullResponseSchema.model_validate(analytic_orm)


async def get_analytic_service(
    analytic_id: UUID,
    user_id: UUID,
    uow: AbstractUnitOfWork,
) -> AnalyticResponseSchema:
    analytic_id = UUID(str(analytic_id))
    user_id = UUID(str(user_id))

    async with uow:
        analytic_orm: AnalyticModel | None = await uow.repository.get_analytic_by_id(analytic_id, user_id)
        if not analytic_orm:
            raise HTTPException(404, detail="Analytic not found")

        return AnalyticResponseSchema.model_validate(analytic_orm)


async def list_analytics_service(
    user_id: UUID,
    uow: AbstractUnitOfWork,
) -> list[AnalyticResponseSchema]:
    user_id = UUID(str(user_id))

    async with uow:
        analytics = await uow.repository.list_analytics(user_id)
        return [AnalyticResponseSchema.model_validate(analytic) for analytic in analytics]


async def delete_analytic_service(
    analytic_id: UUID,
    user_id: UUID,
    s3_client: S3Client,
    uow: AbstractUnitOfWork,
):
    analytic_id = UUID(str(analytic_id))
    user_id = UUID(str(user_id))

    async with uow:
        try:
            analytic_orm: AnalyticModel | None = await uow.repository.get_analytic_by_id(analytic_id, user_id)
            if not analytic_orm:
                raise HTTPException(404, detail="Analytic not found")

            s3_key: str = analytic_orm.dataset_s3_key
            await uow.repository.delete_analytic(analytic_id, user_id)
        except ModelNotFound:
            raise HTTPException(404, detail="Analytic not found")

        await s3_client.delete_file(s3_key)
        await uow.commit()
