from typing import Any

from pydantic import ValidationError

from app.schemas import RecipientIn


def _message(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors():
        field = str(err["loc"][0]) if err["loc"] else "row"
        if field == "name":
            parts.append("name is required" if err["type"] in ("string_too_short", "missing") else "name must be 1-100 characters")
        elif field == "email":
            parts.append("email is required" if err["type"] == "missing" else "email is invalid")
        else:
            parts.append(f"{field} is invalid")
    return "; ".join(parts)


def validate_recipients(rows: list[dict[str, Any]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    valid: list[dict[str, str]] = []
    invalid: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        raw_name = str(row.get("name") or "")[:255]
        raw_email = str(row.get("email") or "")[:320]
        try:
            rec = RecipientIn(**row)
        except (ValidationError, TypeError) as exc:
            msg = _message(exc) if isinstance(exc, ValidationError) else "row is invalid"
            invalid.append({"name": raw_name, "email": raw_email, "error": msg})
            continue
        key = rec.email.lower()
        if key in seen:
            invalid.append({"name": raw_name, "email": raw_email, "error": "duplicate email"})
            continue
        seen.add(key)
        valid.append({"name": rec.name, "email": rec.email})
    return valid, invalid
