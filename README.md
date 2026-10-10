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
