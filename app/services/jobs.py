import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Certificate, Job
from app.services import pdf

logger = logging.getLogger(__name__)


def process_certificate(db: Session, cert: Certificate) -> bool:
    try:
        path = pdf.build_output_path(cert.job_id, cert.id)
        pdf.generate_certificate(cert.recipient_name, cert.job.event_name, cert.job.issue_date, path)
        cert.status = "SUCCESS"
        cert.file_path = path
        cert.error = None
        return True
    except Exception:
        logger.exception("certificate generation failed: %s", cert.id)
        cert.status = "FAILED"
        cert.file_path = None
        cert.error = "certificate generation failed"
        return False


def process_job(db: Session, job_id: str) -> None:
    job = db.get(Job, job_id)
    if job is None:
        return
    try:
        job.status = "PROCESSING"
        db.commit()
        pending = db.query(Certificate).filter_by(job_id=job_id, status="PENDING").all()
        for cert in pending:
            if process_certificate(db, cert):
                job.succeeded += 1
            else:
                job.failed += 1
            db.commit()
        if job.succeeded == 0:
            job.status = "FAILED"
        elif job.failed == 0:
            job.status = "COMPLETED"
        else:
            job.status = "COMPLETED_WITH_ERRORS"
    except Exception:
        logger.exception("job processing crashed: %s", job_id)
        db.rollback()
        job = db.get(Job, job_id)
        job.status = "FAILED"
    job.completed_at = datetime.now(timezone.utc)
    db.commit()


def run_job_in_background(job_id: str) -> None:
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        process_job(db, job_id)
    finally:
        db.close()
