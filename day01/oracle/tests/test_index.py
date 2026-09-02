def test_index_serves_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "The Oracle" in r.text
    assert "/chat" in r.text
