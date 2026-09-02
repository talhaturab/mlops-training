import pytest
from pydantic import ValidationError

from app.schemas import IncomeRequest, MarriageRequest

VALID_INCOME = {
    "country": "Germany",
    "years_pro": 5,
    "ed_level": "Bachelor’s degree (B.A., B.S., B.Eng., etc.)",
    "dev_type": "Data scientist",
    "remote_work": "Remote",
    "age_band": "25-34 years old",
    "org_size": "20 to 99 employees",
    "languages": ["Python"],
}


def test_income_request_accepts_valid_and_defaults_name_to_none():
    req = IncomeRequest(**VALID_INCOME)
    assert req.name is None
    assert req.languages == ["Python"]


def test_income_request_rejects_unknown_enum_value():
    with pytest.raises(ValidationError):
        IncomeRequest(**{**VALID_INCOME, "dev_type": "Wizard"})


def test_income_request_rejects_out_of_range_years():
    with pytest.raises(ValidationError):
        IncomeRequest(**{**VALID_INCOME, "years_pro": 200})


def test_marriage_request_rejects_unknown_status():
    with pytest.raises(ValidationError):
        MarriageRequest(
            age=30,
            relationship_status="married",
            coffee_cups_per_day=2,
            coding_hours_per_week=40,
            side_projects=1,
            unread_slack_messages=10,
        )
