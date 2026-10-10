from app.models import Certificate, Job

PAYLOAD = {
    "event_name": "PyData Workshop",
    "issue_date": "2026-10-01",
    "recipients": [
        {"name": "Asha Rao", "email": "asha@example.com"},
        {"name": "Ravi Kumar", "email": "ravi@example.com"},
    ],
}


def test_create_job_returns_202(client, session_factory):
    resp = client.post("/api/v1/jobs", json=PAYLOAD)
    assert resp.status_code == 202
    body = resp.json()
    assert body["total"] == 2
    assert body["status"] == "PENDING"

    db = session_factory()
    try:
        job = db.get(Job, body["job_id"])
        assert job is not None
        assert job.total == 2
        assert db.query(Certificate).filter_by(job_id=job.id).count() == 2
    finally:
        db.close()
