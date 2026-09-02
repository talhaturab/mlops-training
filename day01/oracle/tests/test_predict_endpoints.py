from datetime import date

VALID_INCOME = {
    "country": "Canada",
    "years_pro": 6,
    "ed_level": "Bachelor’s degree (B.A., B.S., B.Eng., etc.)",
    "dev_type": "Data engineer",
    "remote_work": "Hybrid (some in-person, leans heavy to flexibility)",
    "age_band": "25-34 years old",
    "org_size": "500 to 999 employees",
    "languages": ["Python", "SQL", "Go"],
}

VALID_MARRIAGE = {
    "age": 31,
    "relationship_status": "dating",
    "coffee_cups_per_day": 2,
    "coding_hours_per_week": 45,
    "side_projects": 1,
    "unread_slack_messages": 40,
}


def test_predict_income_returns_prediction_and_metadata(client):
    r = client.post("/predict/income", json=VALID_INCOME)
    assert r.status_code == 200
    body = r.json()
    assert 20_000 < body["predicted_income_usd"] < 500_000
    assert body["model_version"].startswith("income-v")
    assert "survey" in body["disclaimer"].lower()


def test_predict_income_with_name_updates_leaderboard(client):
    client.post("/predict/income", json={**VALID_INCOME, "name": "Ada"})
    board = client.get("/stats").json()["leaderboard"]
    assert board[0]["name"] == "Ada"


def test_predict_income_rejects_bad_enum(client):
    r = client.post("/predict/income", json={**VALID_INCOME, "remote_work": "From the moon"})
    assert r.status_code == 422


def test_predict_marriage_returns_future_date(client):
    r = client.post("/predict/marriage", json=VALID_MARRIAGE)
    assert r.status_code == 200
    body = r.json()
    assert date.fromisoformat(body["predicted_date"]) > date.today()
    assert 0 < body["years_from_now"] <= 30
    assert "invented" in body["disclaimer"].lower()


def test_horoscope_endpoint(client):
    r = client.get("/horoscope", params={"birthday": "1990-08-15"})
    assert r.status_code == 200
    assert r.json()["sign"] == "Leo"
    assert len(r.json()["message"]) > 10


def test_horoscope_rejects_bad_date(client):
    assert client.get("/horoscope", params={"birthday": "not-a-date"}).status_code == 422
