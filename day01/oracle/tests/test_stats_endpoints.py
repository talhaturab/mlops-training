def test_stats_starts_empty(client):
    body = client.get("/stats").json()
    assert body == {"fortunes_told": 0, "leaderboard": []}


def test_options_lists_enums(client):
    body = client.get("/options").json()
    assert "Remote" in body["remote_work"]
    assert "single" in body["relationship_statuses"]
    assert "python" in body["languages"]
    assert "Germany" in body["countries"]
