from app.ml.features import (
    FEATURE_COLUMNS,
    OTHER_COUNTRY,
    build_feature_frame,
    normalize_country,
    normalize_language,
)


def test_normalize_language_strips_parenthetical_and_case():
    assert normalize_language("Bash/Shell (all shells)") == "bash/shell"
    assert normalize_language("Python") == "python"


def test_normalize_country_aliases_and_other():
    assert normalize_country("United States of America") == "United States of America"
    assert normalize_country("usa") == "United States of America"
    assert normalize_country("UK") == "United Kingdom of Great Britain and Northern Ireland"
    assert normalize_country("Narnia") == OTHER_COUNTRY


def test_build_feature_frame_columns_and_flags():
    record = {
        "country": "Germany",
        "years_pro": 7,
        "ed_level": "Master’s degree (M.A., M.S., M.Eng., MBA, etc.)",
        "dev_type": "AI/ML engineer",
        "remote_work": "Remote",
        "age_band": "25-34 years old",
        "org_size": "100 to 499 employees",
        "languages": ["Python", "SQL", "Bash/Shell (all shells)", "COBOL"],
    }
    df = build_feature_frame([record])
    assert list(df.columns) == FEATURE_COLUMNS
    assert df.loc[0, "lang_python"] == 1
    assert df.loc[0, "lang_bash"] == 1
    assert df.loc[0, "lang_rust"] == 0
    assert df.loc[0, "years_pro"] == 7


def test_build_feature_frame_caps_years():
    record = {
        "country": "Germany",
        "years_pro": 99,
        "ed_level": "Master’s degree (M.A., M.S., M.Eng., MBA, etc.)",
        "dev_type": "AI/ML engineer",
        "remote_work": "Remote",
        "age_band": "25-34 years old",
        "org_size": "100 to 499 employees",
        "languages": [],
    }
    assert build_feature_frame([record]).loc[0, "years_pro"] == 50
