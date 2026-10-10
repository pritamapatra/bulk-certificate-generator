import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Certificate, Job
from app.schemas import CertificateOut, JobCreatedOut, JobCreate, JobStatusOut
from app.services.jobs import run_job_in_background
from app.services.validation import validate_recipients

router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.post("/jobs", status_code=202, response_model=JobCreatedOut)
def create_job(
    payload: JobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> JobCreatedOut:
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
        items=[CertificateOut(id=c.id, name=c.recipient_name, status=c.status, error=c.error) for c in certs],
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
