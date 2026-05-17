from uuid import uuid4

import pandas as pd

from src.orm.enums import DataType
from src.tasks.analytic.analyze_columns import (
    analyze_dataset_columns,
    has_datetime,
    to_json_value,
)


def test_numeric_column_analysis():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})

    result = analyze_dataset_columns(df, uuid4())

    col = result[0]

    assert col.data_type == DataType.NUMBER
    assert col.numeric_metrics_json is not None
    assert "mean" in col.numeric_metrics_json
    assert col.string_metrics_json is None
    assert col.date_metrics_json is None


def test_string_column_analysis():
    df = pd.DataFrame({"a": ["x", "y", "x", "z", "x"]})

    result = analyze_dataset_columns(df, uuid4())

    col = result[0]

    assert col.data_type == DataType.STRING
    assert col.string_metrics_json is not None
    assert "top_values" in col.string_metrics_json
    assert col.numeric_metrics_json is None


def test_datetime_column_analysis():
    df = pd.DataFrame({"a": pd.date_range("2024-01-01", periods=5)})

    result = analyze_dataset_columns(df, uuid4())

    col = result[0]

    assert col.data_type == DataType.DATETIME
    assert col.date_metrics_json is not None
    assert "min" in col.date_metrics_json
    assert "max" in col.date_metrics_json


def test_mixed_column_fallback_to_string():
    df = pd.DataFrame({"a": [1, "x", 3, "y", None]})

    result = analyze_dataset_columns(df, uuid4())

    col = result[0]

    assert col.data_type == DataType.STRING


def test_has_datetime_true():
    series = pd.Series(pd.date_range("2024-01-01", periods=10))

    assert has_datetime(series) == True


def test_to_json_value_normal():
    assert to_json_value(10) == 10
    assert to_json_value(10.5) == 10.5
