import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from src.tasks.predict.predict import predict_values, load_ai_model
from catboost import CatboostError


@patch("src.tasks.predict.predict.CatBoostClassifier")
def test_predict_values_success(mock_catboost):
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

    model_instance = mock_catboost.return_value
    model_instance.predict.return_value = [0, 1]

    result = predict_values(df, "fake_model.cbm")

    assert "prediction" in result.columns
    assert list(result["prediction"]) == [0, 1]

    model_instance.predict.assert_called_once_with(df)


@patch("src.tasks.predict.predict.load_ai_model")
def test_predict_values_catboost_error(mock_load):
    df = pd.DataFrame({"a": [1, 2]})

    mock_model = MagicMock()
    mock_model.predict.side_effect = CatboostError("error")

    mock_load.return_value = mock_model

    with pytest.raises(ValueError) as exc:
        predict_values(df, "model.cbm")

    assert "training columns" in str(exc.value)


@patch("src.tasks.predict.predict.CatBoostClassifier")
def test_load_ai_model(mock_catboost):
    instance = mock_catboost.return_value

    model = load_ai_model("model.cbm")

    instance.load_model.assert_called_once_with("model.cbm")
    assert model == instance
