"""Load model artifacts once and expose plain predict functions."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.ml.features import MARRIAGE_FEATURES, build_feature_frame

MIN_MARRIAGE_YEARS = 0.2
MAX_MARRIAGE_YEARS = 30.0


def _load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing model artifact {path}. Run `make train` in day01/oracle to create it."
        )
    return joblib.load(path)


class LoadedModels:
    def __init__(self, artifacts_dir: Path) -> None:
        self._income = _load(artifacts_dir / "income_model.joblib")
        self._marriage = _load(artifacts_dir / "marriage_model.joblib")

    @property
    def income_version(self) -> str:
        return self._income["model_version"]

    @property
    def marriage_version(self) -> str:
        return self._marriage["model_version"]

    def predict_income(self, record: dict) -> float:
        """record has the IncomeRequest fields (minus name). Returns USD per year."""
        X = build_feature_frame([record])
        log_income = self._income["pipeline"].predict(X)[0]
        return float(np.exp(log_income))

    def predict_marriage_years(self, record: dict) -> float:
        X = pd.DataFrame([record], columns=MARRIAGE_FEATURES)
        years = float(self._marriage["pipeline"].predict(X)[0])
        return min(max(years, MIN_MARRIAGE_YEARS), MAX_MARRIAGE_YEARS)
