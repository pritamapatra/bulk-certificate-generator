# Bulk Certificate Generator

A backend API that accepts a list of recipients in one request, generates a PDF certificate for each valid recipient in the background, tracks job progress, and lets clients download certificates individually or as a ZIP.

## Setup

Requires Python 3.14 (see `.python-version`).

```bash
git clone [https://github.com/pritamapatra/bulk-certificate-generator.git](https://github.com/pritamapatra/bulk-certificate-generator.git)
cd bulk-certificate-generator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python -m uvicorn app.main:app --reload
```

- The API is served at http://localhost:8000
- Interactive docs are at http://localhost:8000/docs
- Health check: http://localhost:8000/health

Configuration is read from environment variables, all optional:

| Variable | Default | Purpose |
|---|---|---|
| DATABASE_URL | sqlite:///./app.db | Database connection string (use a postgresql:// URL in production) |
| GENERATED_DIR | generated | Folder where PDFs are written |

## Test

```bash
python -m pytest -q
```

Tests use an in-memory SQLite database and a temporary output folder, so they never touch local data.

## API usage

Set the base URL once. Use the local server, or the deployed one.

```bash
BASE=http://localhost:8000
```

### Create a job

Invalid rows do not reject the request. They are saved as FAILED with an error, and valid rows are still processed.

```bash
curl -s -X POST $BASE/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"event_name":"PyData Workshop","issue_date":"2026-10-01","recipients":[{"name":"Asha Rao","email":"asha@example.com"},{"name":"","email":"bad"}]}'
```

Response (202 Accepted):

```json
{"job_id":"f5125a9c-d4a5-43db-922b-89ec35e1bd04","status":"PENDING","total":2}
```

Save the id for the next calls:

```bash
JOB_ID=f5125a9c-d4a5-43db-922b-89ec35e1bd04
```

### Check job status

```bash
curl -s $BASE/api/v1/jobs/$JOB_ID
```

Response (200 OK):

```json
{
  "job_id": "f5125a9c-d4a5-43db-922b-89ec35e1bd04",
  "status": "COMPLETED_WITH_ERRORS",
  "total": 2,
  "succeeded": 1,
  "failed": 1,
  "items": [
    {"id": "e7f46a79-4f32-4134-9d7e-d6ed51af83f9", "name": "Asha Rao", "status": "SUCCESS", "error": null},
    {"id": "5b53837c-fcee-4a81-9012-0ca7801b7231", "name": "", "status": "FAILED", "error": "name is required; email is invalid"}
  ]
}
```

Job statuses: PENDING, PROCESSING, COMPLETED, COMPLETED_WITH_ERRORS, FAILED. An unknown job id returns 404.

### Download one certificate

Use the id of an item whose status is SUCCESS.

```bash
CERT_ID=e7f46a79-4f32-4134-9d7e-d6ed51af83f9
curl -s -o certificate.pdf $BASE/api/v1/jobs/$JOB_ID/certificates/$CERT_ID
```

Returns a PDF (200). Returns 404 if the certificate is missing, failed, or belongs to a different job.

### Download all certificates as a ZIP

```bash
curl -s -o certificates.zip $BASE/api/v1/jobs/$JOB_ID/download
```

Returns a ZIP of every successful PDF (200). Returns 404 if the job has none.

### Rate limit

`POST /api/v1/jobs` allows 10 requests per minute per IP. The 11th request returns 429.
