import pandas as pd

from training.prepare_data import RAW_COLUMNS, slim


def _row(**overrides):
    base = {
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
    return {**base, **overrides}


def test_slim_keeps_good_rows_and_drops_bad_ones():
    df = pd.DataFrame(
        [
            _row(),
            _row(ConvertedCompYearly=1000.0),  # below salary floor
            _row(ConvertedCompYearly=None),  # missing salary
            _row(Age="Prefer not to say"),  # unusable category
            _row(OrgSize="I don’t know"),  # unusable category
            _row(WorkExp=None),  # missing numeric
        ]
    )
    out = slim(df)
    assert len(out) == 1
    assert list(out.columns) == RAW_COLUMNS
