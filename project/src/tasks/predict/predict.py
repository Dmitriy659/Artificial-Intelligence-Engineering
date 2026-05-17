from functools import lru_cache
from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier, CatboostError

from ...logger.get_logger import get_logger

logger = get_logger(__name__)

EXPECTED_COLUMNS = [
    "person_age",
    "person_gender",
    "person_education",
    "person_income",
    "person_emp_exp",
    "person_home_ownership",
    "loan_amnt",
    "loan_intent",
    "loan_int_rate",
    "loan_percent_income",
    "cb_person_cred_hist_length",
    "credit_score",
    "previous_loan_defaults_on_file",
]


def predict_values(dataset: pd.DataFrame, model_path: Path | str) -> pd.DataFrame:
    model: CatBoostClassifier = load_ai_model(model_path)
    logger.info("Model loaded")

    try:
        dataset: pd.DataFrame = preprocess_dataset(dataset)
        predictions = model.predict(dataset)
        probabilities = model.predict_proba(dataset)
        confidence = probabilities.max(axis=1)

        dataset["prediction"] = predictions
        dataset["prediction_confidence"] = confidence

        return dataset
    except CatboostError:
        raise ValueError(
            "The training columns do not match the training dataset. " "Check the order, columns and types."
        )


def preprocess_dataset(dataset: pd.DataFrame) -> pd.DataFrame:
    for col in EXPECTED_COLUMNS:
        if col not in dataset.columns:
            raise ValueError(f"The column {col} is not present in the dataset.")

    dataset = dataset[EXPECTED_COLUMNS]

    numeric_cols = dataset.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        dataset[col] = dataset[col].fillna(dataset[col].median())

    categorical_cols = dataset.select_dtypes(exclude=["number"]).columns
    for col in categorical_cols:
        dataset[col] = dataset[col].fillna(dataset[col].mode()[0] if not dataset[col].mode().empty else "Unknown")

    return dataset


@lru_cache(maxsize=100)
def load_ai_model(model_path: Path | str) -> CatBoostClassifier:
    model = CatBoostClassifier()
    model.load_model(str(model_path))
    return model
