from app.services import pdf


def test_one_failure_does_not_block_others(client, monkeypatch):
    real = pdf.generate_certificate

    def flaky(name, event, issue_date, out_path, **kwargs):
        if name == "Boom":
            raise RuntimeError("render failed")
        return real(name, event, issue_date, out_path, **kwargs)

    monkeypatch.setattr(pdf, "generate_certificate", flaky)

    resp = client.post("/api/v1/jobs", json={
        "event_name": "PyData Workshop",
        "issue_date": "2026-10-01",
        "recipients": [
            {"name": "Asha Rao", "email": "asha@example.com"},
            {"name": "Boom", "email": "boom@example.com"},
            {"name": "Ravi Kumar", "email": "ravi@example.com"},
        ],
    })
    assert resp.status_code == 202

    data = client.get(f"/api/v1/jobs/{resp.json()['job_id']}").json()
    assert data["status"] == "COMPLETED_WITH_ERRORS"
    assert data["succeeded"] == 2
    assert data["failed"] == 1
    by_name = {i["name"]: i for i in data["items"]}
    assert by_name["Asha Rao"]["status"] == "SUCCESS"
    assert by_name["Ravi Kumar"]["status"] == "SUCCESS"
    assert by_name["Boom"]["status"] == "FAILED"
    assert by_name["Boom"]["error"]
