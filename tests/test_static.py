def test_index_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "Bulk Certificate Generator" in resp.text
