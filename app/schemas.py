from datetime import date
from typing import Annotated, Any

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from app.config import MAX_RECIPIENTS

RecipientName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class RecipientIn(BaseModel):
    name: RecipientName
    email: EmailStr


class JobCreate(BaseModel):
    event_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
    issue_date: date
    recipients: Annotated[list[dict[str, Any]], Field(min_length=1, max_length=MAX_RECIPIENTS)]


class JobCreatedOut(BaseModel):
    job_id: str
    status: str
    total: int


class CertificateOut(BaseModel):
    id: str
    verify_code: str
    name: str
    status: str
    error: str | None = None


class JobStatusOut(BaseModel):
    job_id: str
    status: str
    total: int
    succeeded: int
    failed: int
    items: list[CertificateOut]
