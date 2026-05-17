import datetime
from io import BytesIO
from uuid import UUID

import pandas as pd

from ...adapters.s3_client import S3Client
from ...adapters.unit_work import AbstractUnitOfWork
from ...exceptions import ModelNotFound
from ...orm.enums import AnalyticStatus
from ...orm.models import AnalyticModel, ColumnModel
from .analyze_columns import analyze_dataset_columns


async def analyze_dataset(analytic_id: UUID, s3_client: S3Client, uow: AbstractUnitOfWork):
    async with uow:
        analytic_orm: AnalyticModel | None = await uow.repository.get_analytic_by_id(analytic_id)
        if analytic_orm is None:
            raise ModelNotFound("Analytic not found")
        s3_key: str = analytic_orm.dataset_s3_key

        analytic_orm.status = AnalyticStatus.STARTED
        analytic_orm.started_at = datetime.datetime.now()
        await uow.repository.update_analytic(analytic_orm)
        await uow.commit()

    try:
        file_obj: bytes = await s3_client.download_file(s3_key)
    except Exception as e:
        await fail_analyze(analytic_id, uow, "failed to download file")
        raise e

    try:
        if s3_key.endswith(".csv"):
            df: pd.DataFrame = pd.read_csv(BytesIO(file_obj))
        else:
            df: pd.DataFrame = pd.read_excel(BytesIO(file_obj))
    except Exception as e:
        await fail_analyze(analytic_id, uow, "failed to read file")
        raise e

    if df.empty:
        await fail_analyze(analytic_id, uow, "Empty dataset")
        raise ValueError("Empty dataset")

    try:
        columns_result: list[ColumnModel] = analyze_dataset_columns(df, analytic_id)
    except Exception as e:
        await fail_analyze(analytic_id, uow, "failed to analyze dataset")
        raise e

    try:
        async with uow:
            analytic_orm: AnalyticModel | None = await uow.repository.get_analytic_by_id(analytic_id)
            if analytic_orm is None:
                raise ModelNotFound("Analytic not found")
            await uow.repository.create_columns(columns_result)
            analytic_orm.status = AnalyticStatus.READY
            analytic_orm.ended_at = datetime.datetime.now()
            analytic_orm.analytic_result = "Success analytic"
            await uow.commit()
    except Exception as e:
        await fail_analyze(analytic_id, uow, "failed to update results")
        raise e


async def fail_analyze(analytic_id: UUID, uow: AbstractUnitOfWork, desc: str):
    async with uow:
        analytic_orm: AnalyticModel | None = await uow.repository.get_analytic_by_id(analytic_id)
        if analytic_orm is None:
            raise ModelNotFound("Analytic not found")
        analytic_orm.status = AnalyticStatus.FAILED
        analytic_orm.ended_at = datetime.datetime.now()
        analytic_orm.analytic_result = f"Analytic failed: {desc}"
        await uow.commit()
