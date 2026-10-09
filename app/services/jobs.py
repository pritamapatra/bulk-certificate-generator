import logging

from sqlalchemy.orm import Session

from app.models import Certificate
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
