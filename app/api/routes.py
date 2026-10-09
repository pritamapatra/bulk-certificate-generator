from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Certificate, Job
from app.schemas import JobCreatedOut, JobCreate
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
