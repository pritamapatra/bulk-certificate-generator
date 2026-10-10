import io
import zipfile

BASE = {"event_name": "PyData Workshop", "issue_date": "2026-10-01"}


def _create(client, recipients):
    resp = client.post("/api/v1/jobs", json={**BASE, "recipients": recipients})
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    return job_id, client.get(f"/api/v1/jobs/{job_id}").json()["items"]


def test_single_pdf_download(client):
    job_id, items = _create(client, [{"name": "Asha Rao", "email": "asha@example.com"}])
    resp = client.get(f"/api/v1/jobs/{job_id}/certificates/{items[0]['id']}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


def test_failed_certificate_is_404(client):
    job_id, items = _create(client, [{"name": "Bad", "email": "nope"}])
    assert client.get(f"/api/v1/jobs/{job_id}/certificates/{items[0]['id']}").status_code == 404


def test_unknown_certificate_is_404(client):
    job_id, _ = _create(client, [{"name": "Asha Rao", "email": "asha@example.com"}])
    assert client.get(f"/api/v1/jobs/{job_id}/certificates/unknown").status_code == 404


def test_wrong_job_is_404(client):
    _, items = _create(client, [{"name": "Asha Rao", "email": "asha@example.com"}])
    assert client.get(f"/api/v1/jobs/other/certificates/{items[0]['id']}").status_code == 404


def test_zip_download(client):
    job_id, items = _create(client, [
        {"name": "Asha Rao", "email": "asha@example.com"},
        {"name": "Ravi Kumar", "email": "ravi@example.com"},
        {"name": "Bad", "email": "nope"},
    ])
    resp = client.get(f"/api/v1/jobs/{job_id}/download")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = set(zf.namelist())
    expected = {f"{i['id']}.pdf" for i in items if i["status"] == "SUCCESS"}
    assert len(expected) == 2
    assert names == expected


def test_zip_with_no_success_is_404(client):
    job_id, _ = _create(client, [{"name": "Bad", "email": "nope"}])
    assert client.get(f"/api/v1/jobs/{job_id}/download").status_code == 404


def test_zip_unknown_job_is_404(client):
    assert client.get("/api/v1/jobs/unknown/download").status_code == 404
