from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.tasks.analytic.analyze import analyze_dataset


@pytest.mark.asyncio
@patch("src.tasks.analytic.analyze.analyze_dataset_columns")
@patch("src.tasks.analytic.analyze.pd.read_csv")
@patch("src.tasks.analytic.analyze.S3Client")
async def test_analyze_dataset_success_csv(mock_s3, mock_read_csv, mock_columns):
    analytic_id = uuid4()

    # DF mock
    mock_df = MagicMock()
    mock_df.empty = False
    mock_read_csv.return_value = mock_df

    # columns result
    mock_columns.return_value = ["col1", "col2"]

    # S3
    s3_instance = mock_s3.return_value
    s3_instance.download_file = AsyncMock(return_value=b"filedata")

    # UoW
    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None

    analytic = MagicMock()
    analytic.dataset_s3_key = "file.csv"

    uow.repository.get_analytic_by_id = AsyncMock(return_value=analytic)
    uow.repository.update_analytic = AsyncMock()
    uow.repository.create_columns = AsyncMock()
    uow.commit = AsyncMock()

    await analyze_dataset(analytic_id, s3_instance, uow)

    uow.repository.update_analytic.assert_awaited()
    uow.repository.create_columns.assert_awaited_once()
    uow.commit.assert_awaited()


@pytest.mark.asyncio
@patch("src.tasks.analytic.analyze.pd.read_csv")
@patch("src.tasks.analytic.analyze.S3Client")
async def test_analyze_dataset_empty_df(mock_s3, mock_read_csv):
    analytic_id = uuid4()

    mock_df = MagicMock()
    mock_df.empty = True
    mock_read_csv.return_value = mock_df

    s3_instance = mock_s3.return_value
    s3_instance.download_file = AsyncMock(return_value=b"filedata")

    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    analytic = MagicMock()
    analytic.dataset_s3_key = "file.csv"

    uow.repository.get_analytic_by_id = AsyncMock(return_value=analytic)

    with pytest.raises(ValueError) as exc:
        await analyze_dataset(analytic_id, s3_instance, uow)

    assert "Empty dataset" in str(exc.value)


@pytest.mark.asyncio
@patch("src.tasks.analytic.analyze.fail_analyze", new_callable=AsyncMock)
@patch("src.tasks.analytic.analyze.S3Client")
async def test_analyze_dataset_s3_failure(mock_s3, mock_fail):
    analytic_id = uuid4()

    s3_instance = mock_s3.return_value
    s3_instance.download_file = AsyncMock(side_effect=Exception("S3 down"))

    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    analytic = MagicMock()
    analytic.dataset_s3_key = "file.csv"

    uow.repository.get_analytic_by_id = AsyncMock(return_value=analytic)

    with pytest.raises(Exception):
        await analyze_dataset(analytic_id, s3_instance, uow)

    mock_fail.assert_awaited()


@pytest.mark.asyncio
@patch("src.tasks.analytic.analyze.analyze_dataset_columns")
@patch("src.tasks.analytic.analyze.pd.read_csv")
@patch("src.tasks.analytic.analyze.S3Client")
async def test_analyze_dataset_final_update(mock_s3, mock_read_csv, mock_columns):
    analytic_id = uuid4()

    mock_df = MagicMock()
    mock_df.empty = False
    mock_read_csv.return_value = mock_df

    mock_columns.return_value = ["col1"]

    s3_instance = mock_s3.return_value
    s3_instance.download_file = AsyncMock(return_value=b"filedata")

    uow = AsyncMock()
    uow.__aenter__.return_value = uow

    analytic = MagicMock()
    analytic.dataset_s3_key = "file.csv"

    uow.repository.get_analytic_by_id = AsyncMock(return_value=analytic)
    uow.repository.update_analytic = AsyncMock()
    uow.repository.create_columns = AsyncMock()
    uow.commit = AsyncMock()

    await analyze_dataset(analytic_id, s3_instance, uow)

    assert uow.repository.create_columns.await_count == 1
    assert uow.commit.await_count >= 1
