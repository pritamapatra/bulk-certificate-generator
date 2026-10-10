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

## Design decisions

| Decision | Chosen | Why | Revisit when |
|---|---|---|---|
| Web framework | FastAPI over Django | Less boilerplate, built-in validation and OpenAPI docs | An admin UI or heavy ORM features are needed |
| Background work | FastAPI BackgroundTasks over Celery | No extra infrastructure, costs nothing, simple to deploy | Jobs run for minutes or need retries |
| PDF generation | ReportLab over HTML-to-PDF | Pure Python, no native libraries, easy to deploy on a free host | Designers need rich templates |
| Access control | No auth, rate limiting instead | The brief has no user accounts; 10 requests per minute per IP limits abuse on a public URL | Multi-user use, or a UI is added |
| Hosting | Render over Vercel | A long-lived process keeps background tasks and local files working | Moving to object storage and a queue |
| Database | SQLite locally, Neon Postgres in production | Fast in-memory tests, and a free Postgres that does not expire | Traffic outgrows the free plan |
| Frontend | None, Swagger UI at /docs | The task is a backend API; this saves time for tests | Self-serve users are needed |

### How processing works

`POST /api/v1/jobs` validates the batch, stores a job and one row per recipient, returns 202, and schedules a background task. The task opens its own database session, processes each certificate inside its own try/except, and commits counters after every item. One failure never stops the rest, and the job always ends in a terminal status.

### Known limitations

- Tasks are lost if the server restarts, and only a single process is supported. A job interrupted mid-run stays in PROCESSING.
- Render's free disk is ephemeral. Generated PDFs are wiped on redeploy, so old download links can return 404 and certificates must be regenerated.
- Render's free web service sleeps after 15 minutes idle. The first request afterwards can take 30 to 60 seconds.
- Rate-limit counters are kept in memory, so they reset on restart and are not shared across processes.

### What I learned

- SQLAlchemy 2.1 maps a bare `postgresql://` URL to the `psycopg` v3 driver. The app rewrites it to `postgresql+psycopg2://` so the installed driver is used.
- Free managed Postgres has tight limits. Render's expires after 30 days, so Neon is used instead.
- Always run the server with `python -m uvicorn` inside the virtual environment, so the right interpreter is used.

### Future scope

- Celery or RQ with Redis, or a Postgres-backed queue, for durable and retryable jobs.
- S3 or Cloudflare R2 for certificate storage that survives redeploys.
- Per-client API keys, QR verification at `GET /verify/{uuid}`, CSV upload and email delivery.
