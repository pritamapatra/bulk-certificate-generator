PAYLOAD = {
    "event_name": "PyData Workshop",
    "issue_date": "2026-10-01",
    "recipients": [{"name": "Asha Rao", "email": "asha@example.com"}],
}


def test_eleventh_request_is_429(client):
    for _ in range(10):
        assert client.post("/api/v1/jobs", json=PAYLOAD).status_code == 202
    assert client.post("/api/v1/jobs", json=PAYLOAD).status_code == 429


def test_status_endpoint_is_not_limited(client):
    job_id = client.post("/api/v1/jobs", json=PAYLOAD).json()["job_id"]
    for _ in range(15):
        assert client.get(f"/api/v1/jobs/{job_id}").status_code == 200
