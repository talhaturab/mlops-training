def test_health_reports_status_and_llm_not_configured(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llm_configured"] is False
    assert "models_loaded" in body
