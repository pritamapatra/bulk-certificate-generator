def test_index_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "Bulk Certificate Generator" in resp.text


def test_index_has_form_controls(client):
    html = client.get("/").text
    for element_id in ("event-name", "issue-date", "recipients", "sample-btn", "submit-btn", "result", "progress"):
        assert f'id="{element_id}"' in html
