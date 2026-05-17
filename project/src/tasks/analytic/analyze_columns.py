import datetime
import math
from typing import Any

import pandas as pd

from ...orm.enums import DataType
from ...orm.models import ColumnModel


def analyze_dataset_columns(df: pd.DataFrame, analytic_id) -> list[ColumnModel]:
    columns_analysis: list[ColumnModel] = []

    for col in df.columns:
        series: pd.Series = df[col]
        count: int = int(series.size)
        missing_count: int = int(series.isna().sum())
        missing_percent: float = float(missing_count / count * 100)

        numeric_metrics_json: dict | None = None
        string_metrics_json: dict | None = None
        date_metrics_json: dict | None = None

        if pd.api.types.is_numeric_dtype(series):
            data_type = DataType.NUMBER
            metrics = {
                "mean": to_json_value(series.mean()),
                "median": to_json_value(series.median()),
                "std": to_json_value(series.std()),
                "min": to_json_value(series.min()),
                "max": to_json_value(series.max()),
                "unique_count": int(series.nunique()),
            }
            numeric_metrics_json = metrics

        elif has_datetime(series):
            series = pd.to_datetime(series, errors="coerce")
            count: int = int(series.size)
            missing_count: int = int(series.isna().sum())
            missing_percent: float = float(missing_count / count * 100)

            data_type = DataType.DATETIME
            min_value: datetime.datetime = convert_to_python_datetime(series.min())
            max_value: datetime.datetime = convert_to_python_datetime(series.max())
            metrics = {
                "min": min_value.strftime("%Y-%m-%dT%H:%M:%S") if min_value else None,
                "max": max_value.strftime("%Y-%m-%dT%H:%M:%S") if max_value else None,
                "range_days": (max_value - min_value).days if max_value and min_value else 0,
                "unique_count": int(series.nunique()),
            }
            date_metrics_json = metrics

        else:
            data_type = DataType.STRING
            top_values = {
                str(key): int(value) for key, value in series.value_counts(dropna=True).head(5).to_dict().items()
            }
            metrics = {"unique_count": int(series.nunique()), "top_values": top_values}
            string_metrics_json = metrics

        column_model: ColumnModel = ColumnModel(
            analytic_id=analytic_id,
            column_name=col,
            data_type=data_type,
            count=count,
            missing_count=missing_count,
            missing_percent=missing_percent,
            numeric_metrics_json=numeric_metrics_json,
            string_metrics_json=string_metrics_json,
            date_metrics_json=date_metrics_json,
        )

        columns_analysis.append(column_model)

    return columns_analysis


def has_datetime(series: pd.Series) -> bool:
    series_datetime = pd.to_datetime(series, errors="coerce")
    return series_datetime.notna().sum() / max(1, series.size) > 0.5


def convert_to_python_datetime(time_value: pd.Timestamp) -> datetime.datetime | None:
    if pd.notna(time_value):
        return time_value.to_pydatetime()
    return None


def to_json_value(value: Any) -> float | int | str | None:
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, float) and not math.isfinite(value):
        return None

    return value
