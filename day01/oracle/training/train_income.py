"""Train the income model on the slim survey CSV.

Run:  uv run python -m training.train_income
Writes artifacts/income_model.joblib and artifacts/income_metrics.json.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.ml.features import CATEGORICAL_COLUMNS, FEATURE_COLUMNS, build_feature_frame
from training.prepare_data import SLIM_PATH

PROJECT_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_DIR / "artifacts"


def survey_rows_to_records(df: pd.DataFrame) -> list[dict]:
    """Rename survey columns into the request-shaped dicts that build_feature_frame expects."""
    records = []
    for row in df.itertuples(index=False):
        records.append(
            {
                "country": row.Country,
                "years_pro": int(row.WorkExp),
                "ed_level": row.EdLevel,
                "dev_type": str(row.DevType).split(";")[0],
                "remote_work": row.RemoteWork,
                "age_band": row.Age,
                "org_size": row.OrgSize,
                "languages": str(row.LanguageHaveWorkedWith).split(";"),
            }
        )
    return records


def build_pipeline(random_state: int) -> Pipeline:
    preprocess = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLUMNS)],
        remainder="passthrough",
    )
    model = HistGradientBoostingRegressor(
        max_iter=300, learning_rate=0.05, max_leaf_nodes=31, random_state=random_state
    )
    return Pipeline([("preprocess", preprocess), ("model", model)])


def train(df: pd.DataFrame, random_state: int = 42) -> tuple[Pipeline, dict]:
    X = build_feature_frame(survey_rows_to_records(df))
    y_log = np.log(df["ConvertedCompYearly"].to_numpy())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_log, test_size=0.2, random_state=random_state
    )
    pipeline = build_pipeline(random_state)
    pipeline.fit(X_train, y_train)

    pred_usd = np.exp(pipeline.predict(X_test))
    true_usd = np.exp(y_test)
    abs_err = np.abs(pred_usd - true_usd)
    metrics = {
        "model_version": f"income-v1-{datetime.now(UTC):%Y%m%d}",
        "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "mae_usd": float(abs_err.mean()),
        "median_abs_pct_error": float(np.median(abs_err / true_usd)),
        "feature_columns": FEATURE_COLUMNS,
    }
    return pipeline, metrics


def save(pipeline: Pipeline, metrics: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "model_version": metrics["model_version"],
            "feature_columns": FEATURE_COLUMNS,
        },
        out_dir / "income_model.joblib",
    )
    (out_dir / "income_metrics.json").write_text(json.dumps(metrics, indent=2))


def main(data_path: Path = SLIM_PATH, out_dir: Path = ARTIFACTS_DIR) -> None:
    df = pd.read_csv(data_path)
    pipeline, metrics = train(df)
    save(pipeline, metrics, out_dir)
    print(json.dumps({k: v for k, v in metrics.items() if k != "feature_columns"}, indent=2))


if __name__ == "__main__":
    main()
