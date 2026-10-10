from pathlib import Path

from app.models import Certificate


def test_pdf_is_generated(client, session_factory, tmp_path):
    resp = client.post("/api/v1/jobs", json={
        "event_name": "PyData Workshop",
        "issue_date": "2026-10-01",
        "recipients": [{"name": "Asha Rao", "email": "asha@example.com"}],
    })
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    db = session_factory()
    try:
        cert = db.query(Certificate).filter_by(job_id=job_id).one()
        assert cert.status == "SUCCESS"
        path = Path(cert.file_path)
    finally:
        db.close()

    assert path.is_file()
    assert tmp_path in path.parents
    assert path.read_bytes().startswith(b"%PDF")
