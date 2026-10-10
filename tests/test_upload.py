URL = "/api/v1/jobs/upload"
FORM = {"event_name": "PyData Workshop", "issue_date": "2026-10-01"}


def _post(client, content, form=FORM, name="r.csv"):
    if isinstance(content, str):
        content = content.encode("utf-8")
    return client.post(URL, data=form, files={"file": (name, content, "text/csv")})


def test_bad_row_creates_failed_certificate(client):
    csv_text = "name,email\nAsha Rao,asha@example.com\nRavi Kumar,not-an-email\nMeera Das,meera@example.com\n"
    resp = _post(client, csv_text)
    assert resp.status_code == 202
    body = resp.json()
    assert body["total"] == 3

    status = client.get(f"/api/v1/jobs/{body['job_id']}").json()
    assert status["status"] == "COMPLETED_WITH_ERRORS"
    assert status["succeeded"] == 2
    assert status["failed"] == 1
    failed = [i for i in status["items"] if i["status"] == "FAILED"]
    assert len(failed) == 1
    assert failed[0]["name"] == "Ravi Kumar"
    assert failed[0]["error"] == "email is invalid"


def test_headers_are_case_and_space_insensitive_and_bom_ok(client):
    csv_text = "\ufeff Name , EMAIL \nAsha Rao,asha@example.com\n"
    resp = _post(client, csv_text)
    assert resp.status_code == 202
    assert resp.json()["total"] == 1


def test_missing_required_column_returns_422(client):
    resp = _post(client, "name,phone\nAsha,123\n")
    assert resp.status_code == 422
    assert "name and email" in resp.json()["detail"]


def test_empty_csv_returns_422(client):
    resp = _post(client, "name,email\n")
    assert resp.status_code == 422


def test_invalid_issue_date_returns_422(client):
    resp = _post(client, "name,email\nAsha,asha@example.com\n", form={"event_name": "X", "issue_date": "not-a-date"})
    assert resp.status_code == 422


def test_oversized_file_returns_413(client):
    big = "name,email\n" + ("a" * 1_100_000)
    resp = _post(client, big)
    assert resp.status_code == 413
