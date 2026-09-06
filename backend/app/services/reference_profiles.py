from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app.core.config import get_settings


@dataclass
class ReferenceProfileRecord:
    id: str
    document_type: str
    profile_name: str
    document_hash: str
    profile_summary: dict[str, Any] = field(default_factory=dict)
    characteristics: dict[str, Any] = field(default_factory=dict)
    status: str = "LOCKED"
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    locked_at: datetime | None = None
    last_action: str | None = None


_REFERENCE_PROFILES: dict[str, ReferenceProfileRecord] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _require_lock_secret(authorization_code: str | None, action: str) -> None:
    settings = get_settings()
    secret = (settings.reference_profile_lock_secret or "").strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reference profile lock authorization is not configured.",
        )
    if not authorization_code or authorization_code != secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Lock authorization required before {action}.",
        )


def create_reference_profile_record(
    *,
    document_type: str,
    profile_name: str,
    document_hash: str,
    profile_summary: dict[str, Any],
    characteristics: dict[str, Any],
    created_by: str | None,
    authorization_code: str | None,
) -> ReferenceProfileRecord:
    _require_lock_secret(authorization_code, "creating a reference profile")
    record = ReferenceProfileRecord(
        id=f"REF-{len(_REFERENCE_PROFILES) + 1:06d}",
        document_type=document_type,
        profile_name=profile_name,
        document_hash=document_hash,
        profile_summary=profile_summary or {},
        characteristics=characteristics or {},
        status="LOCKED",
        created_by=created_by,
        created_at=_utc_now(),
        updated_at=_utc_now(),
        locked_at=_utc_now(),
        last_action="REFERENCE_CREATED",
    )
    _REFERENCE_PROFILES[record.id] = record
    return record


def list_reference_profiles() -> list[ReferenceProfileRecord]:
    return list(_REFERENCE_PROFILES.values())


def get_reference_profile(profile_id: str) -> ReferenceProfileRecord | None:
    return _REFERENCE_PROFILES.get(profile_id)


def update_reference_profile_record(
    *,
    profile_id: str,
    profile_name: str | None,
    profile_summary: dict[str, Any] | None,
    characteristics: dict[str, Any] | None,
    authorization_code: str | None,
    current_user: str | None,
) -> ReferenceProfileRecord:
    record = _REFERENCE_PROFILES.get(profile_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference profile was not found.")
    if record.status == "LOCKED":
        _require_lock_secret(authorization_code, "updating a locked reference profile")
    if profile_name is not None:
        record.profile_name = profile_name
    if profile_summary is not None:
        record.profile_summary = profile_summary
    if characteristics is not None:
        record.characteristics = characteristics
    record.updated_at = _utc_now()
    record.last_action = "REFERENCE_UPDATED"
    return record


def unlock_reference_profile_record(
    *,
    profile_id: str,
    authorization_code: str | None,
    current_user: str | None,
) -> ReferenceProfileRecord:
    record = _REFERENCE_PROFILES.get(profile_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference profile was not found.")
    _require_lock_secret(authorization_code, "unlocking a reference profile")
    record.status = "UNLOCKED"
    record.updated_at = _utc_now()
    record.last_action = "REFERENCE_UNLOCKED"
    record.locked_at = None
    return record


def delete_reference_profile_record(*, profile_id: str, authorization_code: str | None, current_user: str | None) -> None:
    record = _REFERENCE_PROFILES.get(profile_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference profile was not found.")
    _require_lock_secret(authorization_code, "deleting a reference profile")
    del _REFERENCE_PROFILES[profile_id]
