BASE = {"event_name": "PyData Workshop", "issue_date": "2026-10-01"}


def _post(client, recipients):
    return client.post("/api/v1/jobs", json={**BASE, "recipients": recipients})


def _status(client, job_id):
    return client.get(f"/api/v1/jobs/{job_id}").json()


def test_empty_list_rejected(client):
    assert _post(client, []).status_code == 422


def test_over_limit_rejected(client):
    rows = [{"name": "A", "email": "a@example.com"}] * 1001
    assert _post(client, rows).status_code == 422


def test_bad_email_fails_only_that_row(client):
    resp = _post(client, [
        {"name": "Good One", "email": "good@example.com"},
        {"name": "Bad Email", "email": "not-an-email"},
    ])
    assert resp.status_code == 202
    data = _status(client, resp.json()["job_id"])
    by_name = {i["name"]: i for i in data["items"]}
    assert by_name["Good One"]["status"] == "SUCCESS"
    assert by_name["Bad Email"]["status"] == "FAILED"
    assert "email" in by_name["Bad Email"]["error"].lower()


def test_blank_name_fails_only_that_row(client):
    resp = _post(client, [
        {"name": "Good One", "email": "good@example.com"},
        {"name": "   ", "email": "blank@example.com"},
    ])
    assert resp.status_code == 202
    data = _status(client, resp.json()["job_id"])
    failed = [i for i in data["items"] if i["status"] == "FAILED"]
    assert len(failed) == 1
    assert "name" in failed[0]["error"].lower()


def test_duplicate_email_flagged(client):
    resp = _post(client, [
        {"name": "First", "email": "same@example.com"},
        {"name": "Second", "email": "same@example.com"},
    ])
    assert resp.status_code == 202
    data = _status(client, resp.json()["job_id"])
    assert data["succeeded"] == 1
    assert data["failed"] == 1
    failed = [i for i in data["items"] if i["status"] == "FAILED"]
    assert failed[0]["error"]
