import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pandas as pd
import pytest
from fastapi import UploadFile, HTTPException

from src.orm.enums import PredictionStatus
from src.orm.models import ORMPrediction
from src.service.predict_service import (
    create_predict_task,
    get_prediction_status,
    get_predictions_list,
    get_prediction_report_service,
    delete_predict_task,
)


def fake_prediction():
    return ORMPrediction(
        id=uuid4(),
        user_id=uuid4(),
        status=PredictionStatus.READY,
        predicted_at=datetime.datetime.now(),
        dataset_name="test.csv",
        report_s3_key="file.csv",
        predict_result="ok",
    )


@patch("src.service.predict_service.predict_values")
@patch("src.service.predict_service.os.remove")
@patch("src.service.predict_service.uuid.uuid4")
@pytest.mark.asyncio
async def test_create_predict_success(mock_uuid, mock_remove, mock_predict):
    mock_uuid.return_value = uuid4()

    mock_predict.return_value = pd.DataFrame({"a": [1, 2, 3]})

    file = MagicMock(spec=UploadFile)
    file.filename = "test.csv"
    file.read = AsyncMock(return_value=b"a,b\n1,2\n3,4")

    s3 = AsyncMock()

    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.repository.add_predict = AsyncMock()
    uow.commit = AsyncMock()

    result = await create_predict_task(
        user_id=uuid4(),
        file=file,
        uow=uow,
        s3_client=s3,
    )

    assert result.dataset_name == "test.csv"
    s3.upload_file_from_fs.assert_awaited_once()
    uow.repository.add_predict.assert_awaited_once()
    uow.commit.assert_awaited_once()


@patch("src.service.predict_service.predict_values", side_effect=ValueError("fail"))
@patch("src.service.predict_service.uuid.uuid4")
@pytest.mark.asyncio
async def test_create_predict_failed(mock_uuid, mock_predict):
    mock_uuid.return_value = uuid4()

    file = MagicMock(spec=UploadFile)
    file.filename = "test.csv"
    file.read = AsyncMock(return_value=b"a,b\n1,2")

    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.repository.add_predict = AsyncMock()
    uow.commit = AsyncMock()

    s3 = AsyncMock()

    result = await create_predict_task(
        user_id=uuid4(),
        file=file,
        uow=uow,
        s3_client=s3,
    )

    assert result.status == PredictionStatus.FAILED
    uow.repository.add_predict.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_prediction_status():
    pred = fake_prediction()

    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.repository.get_predict = AsyncMock(return_value=pred)

    result = await get_prediction_status(
        pred.id,
        pred.user_id,
        uow,
    )

    assert result.id == pred.id


@pytest.mark.asyncio
async def test_get_prediction_not_found():
    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.repository.get_predict = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await get_prediction_status(
            uuid4(),
            uuid4(),
            uow,
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_predictions():
    preds = [fake_prediction(), fake_prediction()]

    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.repository.get_predicts_list = AsyncMock(return_value=preds)

    result = await get_predictions_list(
        user_id=uuid4(),
        uow=uow,
        page=1,
        per_page=10,
    )

    assert len(result.items) == 2
    assert result.page == 1


@pytest.mark.asyncio
async def test_report_service():
    pred = fake_prediction()

    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.repository.get_predict = AsyncMock(return_value=pred)

    result = await get_prediction_report_service(
        pred.user_id,
        pred.id,
        uow,
    )

    assert result == pred.report_s3_key


@pytest.mark.asyncio
async def test_delete_predict():
    pred = fake_prediction()

    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.repository.get_predict = AsyncMock(return_value=pred)
    uow.repository.delete_predict = AsyncMock()
    uow.commit = AsyncMock()

    s3 = AsyncMock()

    await delete_predict_task(
        pred.user_id,
        pred.id,
        uow,
        s3,
    )

    s3.delete_file.assert_awaited_once_with(pred.report_s3_key)
    uow.repository.delete_predict.assert_awaited_once()
    uow.commit.assert_awaited_once()
