from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ReferenceProfileCreate(BaseModel):
    document_type: str = Field(min_length=1, max_length=32)
    profile_name: str = Field(min_length=1, max_length=128)
    document_hash: str = Field(min_length=1, max_length=256)
    profile_summary: dict[str, Any] = Field(default_factory=dict)
    characteristics: dict[str, Any] = Field(default_factory=dict)
    authorization_code: str | None = None
    notes: str | None = None


class ReferenceProfileUpdate(BaseModel):
    profile_name: str | None = Field(default=None, min_length=1, max_length=128)
    profile_summary: dict[str, Any] | None = None
    characteristics: dict[str, Any] | None = None
    authorization_code: str | None = None
    notes: str | None = None


class ReferenceProfileResponse(BaseModel):
    id: str
    document_type: str
    profile_name: str
    status: Literal["LOCKED", "UNLOCKED", "DELETED"]
    document_hash: str
    profile_summary: dict[str, Any]
    characteristics: dict[str, Any]
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    locked_at: datetime | None = None
    is_locked: bool
    last_action: str | None = None
    audit_events: list[dict[str, Any]] = Field(default_factory=list)
