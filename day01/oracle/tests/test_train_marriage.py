import joblib
import pandas as pd

from app.ml.features import MARRIAGE_FEATURES
from training.train_marriage import generate_dataset, main


def test_generate_dataset_shape_and_ranges():
    df = generate_dataset(n=500, seed=1)
    assert list(df.columns) == MARRIAGE_FEATURES + ["years_until_marriage"]
    assert len(df) == 500
    assert df["years_until_marriage"].between(0.2, 30).all()
    assert set(df["relationship_status"]) <= {"single", "dating", "engaged", "it's complicated"}


def test_main_writes_artifact_that_predicts(tmp_path):
    main(out_dir=tmp_path, n=500)
    artifact = joblib.load(tmp_path / "marriage_model.joblib")
    assert artifact["feature_columns"] == MARRIAGE_FEATURES
    X = pd.DataFrame(
        [
            {
                "age": 28,
                "relationship_status": "dating",
                "coffee_cups_per_day": 3,
                "coding_hours_per_week": 40,
                "side_projects": 2,
                "unread_slack_messages": 120,
            }
        ],
        columns=MARRIAGE_FEATURES,
    )
    years = artifact["pipeline"].predict(X)[0]
    assert 0 < years < 30
