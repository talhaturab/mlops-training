import json

import joblib
import pandas as pd

from training.prepare_data import SLIM_PATH
from training.train_income import main, survey_rows_to_records


def test_survey_rows_to_records_maps_columns():
    df = pd.DataFrame(
        [
            {
                "Country": "Germany",
                "WorkExp": 5.0,
                "EdLevel": "Bachelor’s degree (B.A., B.S., B.Eng., etc.)",
                "DevType": "Data scientist",
                "RemoteWork": "Remote",
                "Age": "25-34 years old",
                "OrgSize": "20 to 99 employees",
                "LanguageHaveWorkedWith": "Python;SQL",
                "ConvertedCompYearly": 60000.0,
            }
        ]
    )
    rec = survey_rows_to_records(df)[0]
    assert rec["years_pro"] == 5
    assert rec["languages"] == ["Python", "SQL"]
    assert rec["country"] == "Germany"


def test_main_trains_on_sample_and_writes_artifacts(tmp_path):
    sample = tmp_path / "sample.csv"
    pd.read_csv(SLIM_PATH).sample(300, random_state=0).to_csv(sample, index=False)
    main(data_path=sample, out_dir=tmp_path)

    artifact = joblib.load(tmp_path / "income_model.joblib")
    assert {"pipeline", "model_version", "feature_columns"} <= set(artifact)
    metrics = json.loads((tmp_path / "income_metrics.json").read_text())
    assert metrics["n_train"] + metrics["n_test"] == 300
    assert metrics["mae_usd"] > 0
    assert metrics["model_version"] == artifact["model_version"]
