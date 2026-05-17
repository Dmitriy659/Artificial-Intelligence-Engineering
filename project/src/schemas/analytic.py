from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnalyticResponseSchema(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    started_at: datetime | None
    ended_at: datetime | None
    dataset_name: str
    analytic_result: str | None

    model_config = ConfigDict(from_attributes=True)


class ColumnResponseSchema(BaseModel):
    id: int
    column_name: str
    data_type: str
    count: int
    missing_count: int
    missing_percent: float

    numeric_metrics_json: dict | None = None
    string_metrics_json: dict | None = None
    date_metrics_json: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class AnalyticFullResponseSchema(AnalyticResponseSchema):
    columns: list[ColumnResponseSchema] = []
