"""Generate a synthetic dataset and train the (entirely made-up) marriage date model.

Run:  uv run python -m training.train_marriage
The point of this model is to show the same serving path as the income model with a
second artifact. The data is invented by the formula below.
"""

from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.ml.features import MARRIAGE_FEATURES, RELATIONSHIP_STATUSES

PROJECT_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_DIR / "artifacts"

_STATUS_EFFECT = {"single": 4.0, "dating": 1.5, "engaged": 0.3, "it's complicated": 6.0}


def generate_dataset(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    age = rng.integers(18, 60, n)
    status = rng.choice(RELATIONSHIP_STATUSES, n, p=[0.45, 0.35, 0.1, 0.1])
    coffee = rng.integers(0, 8, n)
    coding_hours = rng.integers(5, 80, n)
    side_projects = rng.integers(0, 10, n)
    unread_slack = rng.integers(0, 2000, n)

    years = (
        2.0
        + 0.15 * np.clip(30 - age, 0, None)
        + np.vectorize(_STATUS_EFFECT.get)(status)
        + 0.2 * coffee
        + 0.05 * coding_hours
        + 0.4 * side_projects
        + 0.002 * unread_slack
        + rng.normal(0, 1.0, n)
    )
    years = np.clip(years, 0.2, 30)

    return pd.DataFrame(
        {
            "age": age,
            "relationship_status": status,
            "coffee_cups_per_day": coffee,
            "coding_hours_per_week": coding_hours,
            "side_projects": side_projects,
            "unread_slack_messages": unread_slack,
            "years_until_marriage": years,
        },
        columns=MARRIAGE_FEATURES + ["years_until_marriage"],
    )


def train(df: pd.DataFrame, seed: int = 42) -> Pipeline:
    preprocess = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), ["relationship_status"])],
        remainder="passthrough",
    )
    model = GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=seed)
    pipeline = Pipeline([("preprocess", preprocess), ("model", model)])
    pipeline.fit(df[MARRIAGE_FEATURES], df["years_until_marriage"])
    return pipeline


def main(out_dir: Path = ARTIFACTS_DIR, n: int = 5000) -> None:
    df = generate_dataset(n=n)
    pipeline = train(df)
    out_dir.mkdir(parents=True, exist_ok=True)
    version = f"marriage-v1-{datetime.now(UTC):%Y%m%d}"
    joblib.dump(
        {"pipeline": pipeline, "model_version": version, "feature_columns": MARRIAGE_FEATURES},
        out_dir / "marriage_model.joblib",
    )
    print(f"trained {version} on {n} synthetic rows -> {out_dir / 'marriage_model.joblib'}")


if __name__ == "__main__":
    main()
