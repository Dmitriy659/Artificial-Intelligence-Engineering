from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..orm.enums import PredictionStatus


class PredictResponseModel(BaseModel):
    id: UUID
    status: PredictionStatus
    predicted_at: datetime | None
    dataset_name: str
    predict_result: str

    model_config = ConfigDict(from_attributes=True)


class ListPredictResponseModel(BaseModel):
    items: list[PredictResponseModel]
    total: int
    page: int
    per_page: int

    model_config = ConfigDict(from_attributes=True)
