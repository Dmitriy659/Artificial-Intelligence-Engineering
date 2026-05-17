from functools import lru_cache
from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier, CatboostError

from ...logger.get_logger import get_logger

logger = get_logger(__name__)


def predict_values(dataset: pd.DataFrame, model_path: Path | str) -> pd.DataFrame:
    model: CatBoostClassifier = load_ai_model(model_path)
    logger.info("Model loaded")

    try:
        predictions = model.predict(dataset)
        dataset["prediction"] = predictions
        return dataset
    except CatboostError:
        raise ValueError("The training columns do not match the training dataset. Check the order, columns and types.")


@lru_cache(maxsize=100)
def load_ai_model(model_path: Path | str) -> CatBoostClassifier:
    model = CatBoostClassifier()
    model.load_model(str(model_path))
    return model
