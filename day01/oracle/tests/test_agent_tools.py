import json

import pytest

from app.agent import tools as tools_module
from app.agent.tools import ORACLE_TOOLS, get_horoscope, predict_income, set_api_base_url

INCOME_ARGS = {
    "country": "Germany",
    "years_pro": 8,
    "ed_level": "Master’s degree (M.A., M.S., M.Eng., MBA, etc.)",
    "dev_type": "AI/ML engineer",
    "remote_work": "Remote",
    "age_band": "25-34 years old",
    "org_size": "100 to 499 employees",
    "languages": ["Python"],
}


def test_three_tools_registered():
    assert {t.name for t in ORACLE_TOOLS} == {
        "get_horoscope",
        "predict_income",
        "predict_marriage_date",
    }


@pytest.fixture
def api_via_test_client(client, monkeypatch):
    # Point the tools' HTTP client at the FastAPI TestClient instead of a real server.
    async def fake_get(path, params=None):
        return client.get(path, params=params).json()

    async def fake_post(path, payload):
        return client.post(path, json=payload).json()

    monkeypatch.setattr(tools_module, "_get", fake_get)
    monkeypatch.setattr(tools_module, "_post", fake_post)


async def test_get_horoscope_tool_calls_api(api_via_test_client):
    out = await get_horoscope.ainvoke({"birthday": "1990-08-15"})
    assert json.loads(out)["sign"] == "Leo"


async def test_predict_income_tool_calls_api(api_via_test_client):
    out = await predict_income.ainvoke({**INCOME_ARGS, "name": "Grace"})
    assert json.loads(out)["predicted_income_usd"] > 10_000


async def test_tool_reports_http_errors_as_text(monkeypatch):
    async def boom(path, payload):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(tools_module, "_post", boom)
    out = await predict_income.ainvoke(INCOME_ARGS)
    assert out.startswith("Tool error")


def test_set_api_base_url():
    previous = tools_module.API_BASE_URL
    try:
        set_api_base_url("http://models:9000/")
        assert tools_module.API_BASE_URL == "http://models:9000"
    finally:
        set_api_base_url(previous)
