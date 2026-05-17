import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.orm.enums import AnalyticStatus, DataType
from src.orm.models import AnalyticModel, ColumnModel
from src.service.analytic_service import create_analytic_service, analyze_analytic_service, list_analytics_service, \
    delete_analytic_service


def fake_analytic_model():
    return AnalyticModel(
        id=uuid4(),
        user_id=uuid4(),
        status=AnalyticStatus.PENDING,
        created_at=datetime.datetime.now(),
        started_at=datetime.datetime.now(),
        ended_at=datetime.datetime.now(),
        dataset_name="test.csv",
        dataset_s3_key="key.csv",
        analytic_result="ok",
    )


def fake_column_model(analytic_id):
    return ColumnModel(
        id=1,
        analytic_id=analytic_id,
        column_name="age",
        data_type=DataType.NUMBER,
        count=100,
        missing_count=0,
        missing_percent=0.0,
        numeric_metrics_json=None,
        string_metrics_json=None,
        date_metrics_json=None,
    )


@pytest.mark.asyncio
async def test_create_analytic_service():
    file = MagicMock()
    file.filename = "data.csv"

    s3 = AsyncMock()

    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    analytic = fake_analytic_model()

    uow.repository.create = AsyncMock(return_value=analytic)
    uow.commit = AsyncMock()

    result = await create_analytic_service(
        user_id=analytic.user_id,
        file=file,
        s3_client=s3,
        uow=uow,
    )

    assert result.id == analytic.id
    assert result.dataset_name == "test.csv"

    s3.upload_file.assert_awaited_once()
    uow.repository.create.assert_awaited_once()
    uow.commit.assert_awaited_once()


@patch("src.service.analytic_service.analyze_dataset", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_analyze_success(mock_task):
    analytic = fake_analytic_model()

    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    uow.repository.get_analytic_by_id = AsyncMock(side_effect=[analytic, analytic])
    uow.commit = AsyncMock()

    s3 = AsyncMock()

    result = await analyze_analytic_service(
        analytic_id=analytic.id,
        user_id=analytic.user_id,
        s3_client=s3,
        uow=uow,
    )

    assert result.id == analytic.id
    mock_task.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_not_found():
    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    uow.repository.get_analytic_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await analyze_analytic_service(
            analytic_id=uuid4(),
            user_id=uuid4(),
            s3_client=AsyncMock(),
            uow=uow,
        )

    assert exc.value.status_code == 404


from src.service.analytic_service import get_analytic_service_full


@pytest.mark.asyncio
async def test_get_full():
    analytic = fake_analytic_model()
    analytic.columns = [
        fake_column_model(analytic.id)
    ]

    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    uow.repository.get_analytic_full = AsyncMock(return_value=analytic)

    result = await get_analytic_service_full(
        analytic.id,
        analytic.user_id,
        uow,
    )

    assert result.id == analytic.id
    assert len(result.columns) == 1


@pytest.mark.asyncio
async def test_get_full():
    analytic = fake_analytic_model()
    analytic.columns = [
        fake_column_model(analytic.id)
    ]

    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    uow.repository.get_analytic_full = AsyncMock(return_value=analytic)

    result = await get_analytic_service_full(
        analytic.id,
        analytic.user_id,
        uow,
    )

    assert result.id == analytic.id
    assert len(result.columns) == 1


@pytest.mark.asyncio
async def test_list():
    analytics = [fake_analytic_model(), fake_analytic_model()]

    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    uow.repository.list_analytics = AsyncMock(return_value=analytics)

    result = await list_analytics_service(
        user_id=uuid4(),
        uow=uow,
    )

    assert len(result) == 2


@pytest.mark.asyncio
async def test_delete():
    analytic = fake_analytic_model()

    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    uow.repository.get_analytic_by_id = AsyncMock(return_value=analytic)
    uow.repository.delete_analytic = AsyncMock()
    uow.commit = AsyncMock()

    s3 = AsyncMock()

    await delete_analytic_service(
        analytic.id,
        analytic.user_id,
        s3,
        uow,
    )

    s3.delete_file.assert_awaited_once_with(analytic.dataset_s3_key)
    uow.repository.delete_analytic.assert_awaited_once()
    uow.commit.assert_awaited_once()
