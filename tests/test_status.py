BASE = {"event_name": "PyData Workshop", "issue_date": "2026-10-01"}


def _create(client, recipients):
    resp = client.post("/api/v1/jobs", json={**BASE, "recipients": recipients})
    assert resp.status_code == 202
    return resp.json()["job_id"]


def test_mixed_job_reports_counts(client):
    job_id = _create(client, [
        {"name": "Asha Rao", "email": "asha@example.com"},
        {"name": "Ravi Kumar", "email": "ravi@example.com"},
        {"name": "Bad Email", "email": "nope"},
    ])
    data = client.get(f"/api/v1/jobs/{job_id}").json()
    assert data["status"] == "COMPLETED_WITH_ERRORS"
    assert data["total"] == 3
    assert data["succeeded"] == 2
    assert data["failed"] == 1
    assert data["succeeded"] + data["failed"] == data["total"]
    statuses = {i["name"]: i["status"] for i in data["items"]}
    assert statuses == {"Asha Rao": "SUCCESS", "Ravi Kumar": "SUCCESS", "Bad Email": "FAILED"}


def test_all_success_is_completed(client):
    job_id = _create(client, [{"name": "Asha Rao", "email": "asha@example.com"}])
    data = client.get(f"/api/v1/jobs/{job_id}").json()
    assert data["status"] == "COMPLETED"
    assert data["succeeded"] == 1
    assert data["failed"] == 0
    assert data["items"][0]["error"] is None


def test_unknown_job_is_404(client):
    assert client.get("/api/v1/jobs/unknown").status_code == 404
