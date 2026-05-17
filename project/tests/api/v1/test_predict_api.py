from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.api.v1.predict_api import predict_router


def base_predict():
    return {
        "id": str(uuid4()),
        "status": "READY",
        "created_at": "2026-01-01T00:00:00",
        "predicted_at": "2026-01-01T00:00:00",
        "dataset_name": "test.csv",
        "predict_result": "ok",
    }


@patch("src.api.v1.predict_api.create_predict_task", new_callable=AsyncMock)
@patch("src.api.v1.predict_api.S3Client")
@patch("src.api.v1.predict_api.unit_work.SqlAlchemyUnitOfWork")
def test_create_predict_success(mock_uow, mock_s3, mock_service, client_factory):
    client = client_factory([predict_router])
    mock_service.return_value = base_predict()

    response = client.post(
        "/predict/",
        files={"file": ("test.csv", b"a,b", "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "READY"

    mock_service.assert_awaited_once()


def test_create_predict_invalid_file(client_factory):
    client = client_factory([predict_router])
    response = client.post(
        "/predict/",
        files={"file": ("test.txt", b"x", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File must be .csv or .xlsx"


@patch("src.api.v1.predict_api.get_prediction_status", new_callable=AsyncMock)
@patch("src.api.v1.predict_api.unit_work.SqlAlchemyUnitOfWork")
def test_get_prediction_success(mock_uow, mock_service, client_factory):
    client = client_factory([predict_router])
    predict_id = uuid4()

    mock_service.return_value = base_predict()

    response = client.get(f"/predict/{predict_id}")

    assert response.status_code == 200
    assert response.json()["id"] is not None

    mock_service.assert_awaited_once()


@patch("src.api.v1.predict_api.get_predictions_list", new_callable=AsyncMock)
@patch("src.api.v1.predict_api.unit_work.SqlAlchemyUnitOfWork")
def test_get_predictions_list(mock_uow, mock_service, client_factory):
    client = client_factory([predict_router])
    mock_service.return_value = {
        "items": [base_predict(), base_predict()],
        "total": 2,
        "page": 1,
        "per_page": 20,
    }

    response = client.get("/predict/?page=1&per_page=20")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2

    mock_service.assert_awaited_once()


@patch("src.api.v1.predict_api.get_prediction_report_service", new_callable=AsyncMock)
@patch("src.api.v1.predict_api.S3Client")
@patch("src.api.v1.predict_api.unit_work.SqlAlchemyUnitOfWork")
def test_get_prediction_report(mock_uow, mock_s3, mock_service, client_factory):
    client = client_factory([predict_router])
    predict_id = uuid4()

    mock_service.return_value = "fake-key"

    fake_stream = iter([b"chunk1", b"chunk2"])

    mock_s3.return_value.get_file_stream = AsyncMock(return_value=fake_stream)

    response = client.get(f"/predict/{predict_id}/report")

    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment")


@patch("src.api.v1.predict_api.delete_predict_task", new_callable=AsyncMock)
@patch("src.api.v1.predict_api.S3Client")
@patch("src.api.v1.predict_api.unit_work.SqlAlchemyUnitOfWork")
def test_delete_prediction(mock_uow, mock_s3, mock_service, client_factory):
    client = client_factory([predict_router])
    predict_id = uuid4()

    mock_service.return_value = {"message": "deleted"}

    response = client.delete(f"/predict/{predict_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "deleted"

    mock_service.assert_awaited_once()
