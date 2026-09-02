import pytest

from app.config import Settings
from app.ml.predict import LoadedModels

INCOME_RECORD = {
    "country": "United States of America",
    "years_pro": 10,
    "ed_level": "Master’s degree (M.A., M.S., M.Eng., MBA, etc.)",
    "dev_type": "AI/ML engineer",
    "remote_work": "Remote",
    "age_band": "35-44 years old",
    "org_size": "1,000 to 4,999 employees",
    "languages": ["Python", "SQL"],
}

MARRIAGE_RECORD = {
    "age": 28,
    "relationship_status": "single",
    "coffee_cups_per_day": 4,
    "coding_hours_per_week": 50,
    "side_projects": 3,
    "unread_slack_messages": 500,
}


@pytest.fixture(scope="module")
def models():
    return LoadedModels(Settings(_env_file=None).artifacts_dir)


def test_income_prediction_is_in_a_sane_range(models):
    usd = models.predict_income(INCOME_RECORD)
    assert 30_000 < usd < 500_000
    assert models.income_version.startswith("income-v")


def test_more_experience_in_the_us_earns_more_than_none(models):
    junior = models.predict_income({**INCOME_RECORD, "years_pro": 0, "age_band": "18-24 years old"})
    senior = models.predict_income(INCOME_RECORD)
    assert senior > junior


def test_marriage_years_positive(models):
    years = models.predict_marriage_years(MARRIAGE_RECORD)
    assert 0.2 <= years <= 30
    assert models.marriage_version.startswith("marriage-v")


def test_missing_artifact_gives_helpful_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="make train"):
        LoadedModels(tmp_path)


def test_health_reports_models_loaded(client):
    assert client.get("/health").json()["models_loaded"] is True
