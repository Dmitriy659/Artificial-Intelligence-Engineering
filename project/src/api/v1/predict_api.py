from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from ...adapters import unit_work
from ...adapters.s3_client import S3Client
from ...schemas.predict_schemas import ListPredictResponseModel, PredictResponseModel
from ...service.predict_service import (
    create_predict_task,
    delete_predict_task,
    get_prediction_report_service,
    get_prediction_status,
    get_predictions_list,
)
from ...settings.settings import S3Settings
from ..auth import get_current_user

predict_router = APIRouter(prefix="/predict", tags=["predict"])


@predict_router.post("/", response_model=PredictResponseModel)
async def predict_model(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="File must be .csv or .xlsx")

    s3_client: S3Client = S3Client(S3Settings())
    user_id = user["sub"]

    return await create_predict_task(user_id, file, unit_work.SqlAlchemyUnitOfWork(), s3_client)


@predict_router.get("/{predict_id}", response_model=PredictResponseModel)
async def get_prediction(
    predict_id: UUID,
    user=Depends(get_current_user),
):
    user_id = user["sub"]

    return await get_prediction_status(predict_id, user_id, unit_work.SqlAlchemyUnitOfWork())


@predict_router.get("/", response_model=ListPredictResponseModel)
async def get_predictions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
):
    user_id = user["sub"]

    return await get_predictions_list(
        user_id=user_id,
        page=page,
        per_page=per_page,
        uow=unit_work.SqlAlchemyUnitOfWork(),
    )


@predict_router.get("/{predict_id}/report")
async def get_prediction_report(
    predict_id: UUID,
    user=Depends(get_current_user),
):
    user_id = user["sub"]

    s3_client = S3Client(S3Settings())

    key = await get_prediction_report_service(
        user_id,
        predict_id,
        unit_work.SqlAlchemyUnitOfWork(),
    )

    stream = await s3_client.get_file_stream(key)

    return StreamingResponse(
        stream,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{key}"'},
    )


@predict_router.delete("/{predict_id}")
async def delete_prediction(
    predict_id: UUID,
    user=Depends(get_current_user),
):
    user_id = user["sub"]
    s3_client: S3Client = S3Client(S3Settings())

    return await delete_predict_task(user_id, predict_id, unit_work.SqlAlchemyUnitOfWork(), s3_client)
