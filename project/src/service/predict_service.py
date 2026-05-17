import datetime
import os
import tempfile
import uuid
from io import BytesIO, StringIO
from uuid import UUID

import pandas as pd
from fastapi import HTTPException, UploadFile

from ..adapters.s3_client import S3Client
from ..adapters.unit_work import AbstractUnitOfWork
from ..logger.get_logger import get_logger
from ..orm.enums import PredictionStatus
from ..orm.models import ORMPrediction
from ..schemas.predict_schemas import ListPredictResponseModel, PredictResponseModel
from ..tasks.predict.predict import predict_values

logger = get_logger(__name__)


async def create_predict_task(
    user_id: UUID,
    file: UploadFile,
    uow: AbstractUnitOfWork,
    s3_client: S3Client,
) -> PredictResponseModel:
    filename, extension = os.path.splitext(file.filename)
    content: bytes = await file.read()

    if extension.endswith("csv"):
        df: pd.DataFrame = pd.read_csv(StringIO(content.decode("utf-8")))
    else:
        df: pd.DataFrame = pd.read_excel(BytesIO(content))
    logger.info("File was read")

    try:
        result_df: pd.DataFrame = predict_values(df, "./artifacts/catboost_final.cbm")

        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

            if extension == ".csv":
                result_df.to_csv(tmpfile_path, index=False)
            else:
                result_df.to_excel(tmpfile_path, index=False)

        s3_key = f"{uuid.uuid4()}{extension}"
        await s3_client.upload_file_from_fs(tmpfile_path, s3_key)
        os.remove(tmpfile_path)

        async with uow:
            predict_orm: ORMPrediction = ORMPrediction(
                id=uuid.uuid4(),
                user_id=user_id,
                status=PredictionStatus.READY,
                predicted_at=datetime.datetime.now(),
                dataset_name=f"{filename}{extension}",
                report_s3_key=s3_key,
                predict_result="Success",
            )
            await uow.repository.add_predict(predict_orm)
            await uow.commit()
    except ValueError as e:
        async with uow:
            predict_orm: ORMPrediction = ORMPrediction(
                id=uuid.uuid4(),
                user_id=user_id,
                status=PredictionStatus.FAILED,
                predicted_at=datetime.datetime.now(),
                dataset_name=f"{filename}{extension}",
                predict_result=str(e),
            )
            await uow.repository.add_predict(predict_orm)
            await uow.commit()

    return PredictResponseModel.model_validate(predict_orm)


async def get_prediction_status(
    predict_id: UUID,
    user_id: UUID,
    uow: AbstractUnitOfWork,
) -> PredictResponseModel:
    async with uow:
        orm_prediction: ORMPrediction = await uow.repository.get_predict(user_id, predict_id)

        if not orm_prediction:
            raise HTTPException(status_code=404)

        return PredictResponseModel.model_validate(orm_prediction)


async def get_predictions_list(
    user_id: UUID,
    uow: AbstractUnitOfWork,
    page: int,
    per_page: int,
) -> ListPredictResponseModel:
    async with uow:
        offset = (page - 1) * per_page

        prediction_list: list[ORMPrediction] = await uow.repository.get_predicts_list(user_id, offset, per_page)

        prediction_list_dto: list[PredictResponseModel] = [
            PredictResponseModel.model_validate(prediction) for prediction in prediction_list
        ]

    return ListPredictResponseModel(
        items=prediction_list_dto,
        total=len(prediction_list),
        page=page,
        per_page=per_page,
    )


async def get_prediction_report_service(
    user_id: UUID,
    predict_id: UUID,
    uow: AbstractUnitOfWork,
):
    async with uow:
        predict_orm: ORMPrediction | None = await uow.repository.get_predict(user_id, predict_id)

        if not predict_orm or not predict_orm.report_s3_key:
            raise HTTPException(status_code=404, detail="Prediction report not found")
        report_s3_key = predict_orm.report_s3_key

    return report_s3_key


async def delete_predict_task(
    user_id: UUID,
    predict_id: UUID,
    uow: AbstractUnitOfWork,
    s3_client: S3Client,
):
    async with uow:
        orm_prediction: ORMPrediction = await uow.repository.get_predict(user_id, predict_id)

        if not orm_prediction:
            raise HTTPException(status_code=404, detail="Prediction not found")
        await uow.repository.delete_predict(user_id, predict_id)
        if orm_prediction.report_s3_key:
            await s3_client.delete_file(orm_prediction.report_s3_key)
        await uow.commit()
