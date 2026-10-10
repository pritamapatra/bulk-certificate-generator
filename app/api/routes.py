import csv
import io
import os
import zipfile

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.limiter import limiter
from app.models import Certificate, Job
from app.schemas import CertificateOut, JobCreatedOut, JobCreate, JobStatusOut, VerifyOut
from app.services.jobs import run_job_in_background
from app.services.validation import validate_recipients

router = APIRouter(prefix="/api/v1", tags=["jobs"])


MAX_CSV_BYTES = 1_000_000


def _create_job(db: Session, background_tasks: BackgroundTasks, payload: JobCreate) -> JobCreatedOut:
    valid, invalid = validate_recipients(payload.recipients)
    job = Job(
        event_name=payload.event_name,
        issue_date=payload.issue_date,
        status="PENDING",
        total=len(payload.recipients),
        failed=len(invalid),
    )
    db.add(job)
    db.flush()
    for r in valid:
        db.add(Certificate(job_id=job.id, recipient_name=r["name"], recipient_email=r["email"], status="PENDING"))
    for r in invalid:
        db.add(
            Certificate(
                job_id=job.id,
                recipient_name=r["name"],
                recipient_email=r["email"],
                status="FAILED",
                error=r["error"],
            )
        )
    db.commit()
    background_tasks.add_task(run_job_in_background, job.id)
    return JobCreatedOut(job_id=job.id, status=job.status, total=job.total)


@router.post("/jobs", status_code=202, response_model=JobCreatedOut)
@limiter.limit("10/minute")
def create_job(
    request: Request,
    payload: JobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> JobCreatedOut:
    return _create_job(db, background_tasks, payload)


@router.post("/jobs/upload", status_code=202, response_model=JobCreatedOut)
@limiter.limit("10/minute")
def upload_job(
    request: Request,
    background_tasks: BackgroundTasks,
    event_name: str = Form(...),
    issue_date: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> JobCreatedOut:
    raw = file.file.read(MAX_CSV_BYTES + 1)
    if len(raw) > MAX_CSV_BYTES:
        raise HTTPException(status_code=413, detail="CSV file is too large")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="CSV must be UTF-8 encoded")
    try:
        reader = csv.DictReader(io.StringIO(text))
        headers = {(h or "").strip().lower() for h in (reader.fieldnames or [])}
        if not {"name", "email"} <= headers:
            raise HTTPException(status_code=422, detail="CSV must have name and email columns")
        rows = []
        for rec in reader:
            norm = {(k or "").strip().lower(): v for k, v in rec.items() if k is not None}
            rows.append({"name": norm.get("name") or "", "email": norm.get("email") or ""})
    except csv.Error:
        raise HTTPException(status_code=422, detail="CSV could not be parsed")
    try:
        payload = JobCreate(event_name=event_name, issue_date=issue_date, recipients=rows)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=exc.errors(include_url=False, include_context=False, include_input=False),
        )
    return _create_job(db, background_tasks, payload)


@router.get("/jobs/{job_id}", response_model=JobStatusOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobStatusOut:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    certs = sorted(job.certificates, key=lambda c: c.created_at)
    return JobStatusOut(
        job_id=job.id,
        status=job.status,
        total=job.total,
        succeeded=job.succeeded,
        failed=job.failed,
        items=[CertificateOut(id=c.id, verify_code=c.verification_code, name=c.recipient_name, status=c.status, error=c.error) for c in certs],
    )


@router.get("/jobs/{job_id}/certificates/{cert_id}")
def download_certificate(job_id: str, cert_id: str, db: Session = Depends(get_db)) -> FileResponse:
    cert = db.get(Certificate, cert_id)
    if (
        cert is None
        or cert.job_id != job_id
        or cert.status != "SUCCESS"
        or not cert.file_path
        or not os.path.isfile(cert.file_path)
    ):
        raise HTTPException(status_code=404, detail="Certificate not found")
    return FileResponse(cert.file_path, media_type="application/pdf", filename=f"{cert.id}.pdf")


@router.get("/jobs/{job_id}/download")
def download_zip(job_id: str, db: Session = Depends(get_db)) -> Response:
    certs = db.scalars(
        select(Certificate).where(Certificate.job_id == job_id, Certificate.status == "SUCCESS")
    ).all()
    files = [c for c in certs if c.file_path and os.path.isfile(c.file_path)]
    if not files:
        raise HTTPException(status_code=404, detail="No certificates available")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for c in files:
            zf.write(c.file_path, arcname=f"{c.id}.pdf")
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{job_id}.zip"'},
    )


verify_router = APIRouter(tags=["verify"])


@verify_router.get("/verify/{code}", response_model=VerifyOut)
def verify_certificate(code: str, db: Session = Depends(get_db)) -> VerifyOut:
    cert = db.get(Certificate, code)
    if cert is None or cert.status != "SUCCESS":
        raise HTTPException(status_code=404, detail="Certificate not found")
    return VerifyOut(
        name=cert.recipient_name,
        event_name=cert.job.event_name,
        issue_date=cert.job.issue_date,
        status=cert.status,
    )
