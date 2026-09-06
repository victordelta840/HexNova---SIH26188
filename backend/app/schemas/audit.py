from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    event_type: str
    module_name: str
    status: str
    timestamp: datetime
    details: str
    actor_id: str | None = None
    actor_role: str | None = None


class CaseHistoryResponse(BaseModel):
    case_id: str
    document_type: str
    document_hash: str | None
    screening_timestamp: datetime
    completed_at: datetime | None
    screening_status: str
    risk_score: int | None
    risk_level: str | None
    mode: Literal["DEMONSTRATION"]
    integrity_ledger: Literal["database-backed demonstration", "in-memory demonstration"]
    modules: list[dict[str, str]]
    audit_events: list[AuditEventResponse]
    ocr: dict | None = None
    validation: list[dict] | None = None
    tampering: dict | None = None
    metadata: dict | None = None
    face_comparison: dict | None = None
    risk: dict | None = None


class CaseSummaryResponse(BaseModel):
    case_id: str
    document_type: str
    risk_level: str | None
    risk_score: int | None
    screening_status: str
    created_at: datetime
    completed_at: datetime | None
    mode: Literal["DEMONSTRATION"]
    is_demo: bool = False


class CaseListResponse(BaseModel):
    items: list[CaseSummaryResponse]
    page: int
    page_size: int
    total: int


class IntegrityVerificationResponse(BaseModel):
    match: bool
    current_hash: str
    expected_hash: str | None
    status: Literal["INTEGRITY_VERIFIED", "INTEGRITY_MISMATCH"]
    message: str