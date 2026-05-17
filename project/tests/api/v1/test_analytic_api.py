from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.api.v1.analytic_api import analytic_router


def base_analytic():
    return {
        "id": str(uuid4()),
        "status": "created",
        "created_at": "2026-01-01T00:00:00",
        "started_at": "2026-01-01T00:00:01",
        "ended_at": "2026-01-01T00:00:02",
        "dataset_name": "test.csv",
        "analytic_result": "ok",
    }


def base_column():
    return {
        "id": 1,
        "column_name": "age",
        "data_type": "int",
        "count": 100,
        "missing_count": 0,
        "missing_percent": 0.0,
        "numeric_metrics_json": None,
        "string_metrics_json": None,
        "date_metrics_json": None,
    }


@patch("src.api.v1.analytic_api.create_analytic_service", new_callable=AsyncMock)
@patch("src.api.v1.analytic_api.S3Client")
@patch("src.api.v1.analytic_api.unit_work.SqlAlchemyUnitOfWork")
def test_create_analytic_success(
    mock_uow,
    mock_s3,
    mock_service,
    client_factory,
):
    client = client_factory([analytic_router])
    mock_service.return_value = base_analytic()

    response = client.post(
        "/analytic/",
        files={"file": ("test.csv", b"col1,col2", "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "created"

    mock_service.assert_awaited_once()


def test_create_analytic_invalid_extension(client_factory):
    client = client_factory([analytic_router])
    response = client.post(
        "/analytic/",
        files={"file": ("test.txt", b"invalid", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File must be .csv or .xlsx"


@patch("src.api.v1.analytic_api.analyze_analytic_service", new_callable=AsyncMock)
@patch("src.api.v1.analytic_api.S3Client")
@patch("src.api.v1.analytic_api.unit_work.SqlAlchemyUnitOfWork")
def test_analyze_analytic_success(mock_uow, mock_s3, mock_service, client_factory):
    client = client_factory([analytic_router])
    analytic_id = uuid4()

    mock_service.return_value = {
        **base_analytic(),
        "id": str(analytic_id),
        "status": "analyzed",
    }

    response = client.post(f"/analytic/{analytic_id}/analyze")

    assert response.status_code == 200
    assert response.json()["status"] == "analyzed"

    mock_service.assert_awaited_once()


@patch("src.api.v1.analytic_api.list_analytics_service", new_callable=AsyncMock)
@patch("src.api.v1.analytic_api.unit_work.SqlAlchemyUnitOfWork")
def test_list_analytics_success(mock_uow, mock_service, client_factory):
    client = client_factory([analytic_router])
    mock_service.return_value = [
        {**base_analytic(), "status": "created"},
        {**base_analytic(), "status": "completed"},
    ]

    response = client.get("/analytic/")

    assert response.status_code == 200
    assert len(response.json()) == 2

    mock_service.assert_awaited_once()


@patch("src.api.v1.analytic_api.get_analytic_service", new_callable=AsyncMock)
@patch("src.api.v1.analytic_api.unit_work.SqlAlchemyUnitOfWork")
def test_get_analytic_success(mock_uow, mock_service, client_factory):
    client = client_factory([analytic_router])
    analytic_id = uuid4()

    mock_service.return_value = {
        **base_analytic(),
        "id": str(analytic_id),
    }

    response = client.get(f"/analytic/{analytic_id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(analytic_id)

    mock_service.assert_awaited_once()


@patch("src.api.v1.analytic_api.get_analytic_service_full", new_callable=AsyncMock)
@patch("src.api.v1.analytic_api.unit_work.SqlAlchemyUnitOfWork")
def test_get_analytic_full_success(mock_uow, mock_service, client_factory):
    client = client_factory([analytic_router])
    analytic_id = uuid4()

    mock_service.return_value = {
        **base_analytic(),
        "id": str(analytic_id),
        "status": "completed",
        "columns": [base_column()],
    }

    response = client.get(f"/analytic/{analytic_id}/full")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert len(response.json()["columns"]) == 1

    mock_service.assert_awaited_once()


@patch("src.api.v1.analytic_api.delete_analytic_service", new_callable=AsyncMock)
@patch("src.api.v1.analytic_api.S3Client")
@patch("src.api.v1.analytic_api.unit_work.SqlAlchemyUnitOfWork")
def test_delete_analytic_success(mock_uow, mock_s3, mock_service, client_factory):
    client = client_factory([analytic_router])
    analytic_id = uuid4()

    mock_service.return_value = {"message": "deleted"}

    response = client.delete(f"/analytic/{analytic_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "deleted"

    mock_service.assert_awaited_once()
