from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from catboost import CatboostError

from src.tasks.predict.predict import load_ai_model, predict_values


def fake_dataset() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "person_age": [22, 23],
            "person_gender": ["male", "female"],
            "person_education": ["Bachelor", "Master"],
            "person_income": [50000, 60000],
            "person_emp_exp": [1, 2],
            "person_home_ownership": ["RENT", "OWN"],
            "loan_amnt": [1000, 2000],
            "loan_intent": ["PERSONAL", "EDUCATION"],
            "loan_int_rate": [10.5, 12.3],
            "loan_percent_income": [0.2, 0.3],
            "cb_person_cred_hist_length": [3, 4],
            "credit_score": [600, 650],
            "previous_loan_defaults_on_file": ["No", "Yes"],
        }
    )


@patch("src.tasks.predict.predict.load_ai_model")
def test_predict_values_success(mock_load):
    df = fake_dataset()

    model = MagicMock()

    model.predict.return_value = [0, 1]

    proba = MagicMock()
    proba.max.return_value = np.array([0.8, 0.7])

    model.predict_proba.return_value = proba

    mock_load.return_value = model

    result = predict_values(df, "fake_model.cbm")

    assert "prediction" in result.columns
    assert "prediction_confidence" in result.columns

    assert list(result["prediction"]) == [0, 1]
    assert list(result["prediction_confidence"]) == [0.8, 0.7]

    model.predict.assert_called_once()
    model.predict_proba.assert_called_once()
    proba.max.assert_called_once_with(axis=1)


@patch("src.tasks.predict.predict.load_ai_model")
def test_predict_values_catboost_error(mock_load):
    df = fake_dataset()

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
