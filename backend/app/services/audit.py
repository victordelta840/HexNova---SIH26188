import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4
from app.schemas.audit import AuditEventResponse, CaseHistoryResponse, CaseListResponse, CaseSummaryResponse


@dataclass
class AuditEventRecord:
    event_type: str
    module_name: str
    status: str
    timestamp: datetime
    details: str
    actor_id: str | None = None
    actor_role: str | None = None


@dataclass
class CaseRecord:
    case_id: str
    document_type: str
    document_hash: str | None
    screening_timestamp: datetime
    completed_at: datetime | None = None
    screening_status: str = "PROCESSING"
    risk_score: int | None = None
    risk_level: str | None = None
    modules: list[dict[str, str]] = field(default_factory=list)
    events: list[AuditEventRecord] = field(default_factory=list)
    details: dict | None = None
    is_demo: bool = False


class AuditRepository:
    """Storage boundary for database audit persistence and future ledger adapters."""

    def __init__(self) -> None:
        self._cases: dict[str, CaseRecord] = {}
        self._reference_events: dict[str, list[AuditEventRecord]] = {}

    def start_case(self, case_id: str, document_type: str, actor_id: str | None = None, actor_role: str | None = None, is_demo: bool = False) -> CaseRecord:
        case = CaseRecord(case_id, document_type, None, utc_now(), is_demo=is_demo)
        self._cases[case_id] = case
        self.record_event(case_id, "SCREENING_STARTED", "screening", "STARTED", "Case created.", actor_id, actor_role)
        return case

    def set_document_hash(self, case_id: str, document_hash: str) -> None:
        self._cases[case_id].document_hash = document_hash

    def record_event(self, case_id: str, event_type: str, module_name: str, status: str, details: str, actor_id: str | None = None, actor_role: str | None = None) -> None:
        case = self._cases[case_id]
        case.events.append(AuditEventRecord(event_type, module_name, status, utc_now(), details, actor_id, actor_role))
        case.modules.append({"module": module_name, "status": status})

    def complete_case(self, case_id: str, risk_score: int, risk_level: str, details: dict | None = None) -> None:
        case = self._cases[case_id]
        case.risk_score = risk_score
        case.risk_level = risk_level
        case.completed_at = utc_now()
        case.screening_status = "COMPLETED"
        case.details = details

    def fail_case(self, case_id: str, module_name: str, details: str) -> None:
        case = self._cases[case_id]
        case.screening_status = "SCREENING_FAILED"
        self.record_event(case_id, "SCREENING_FAILED", module_name, "FAILED", details)

    def record_reference_event(self, profile_id: str, event_type: str, details: str, actor_id: str | None = None, actor_role: str | None = None) -> None:
        event = AuditEventRecord(event_type, "reference_profile", "COMPLETED", utc_now(), details, actor_id, actor_role)
        self._reference_events.setdefault(profile_id, []).append(event)

    def get_reference_events(self, profile_id: str) -> list[AuditEventRecord]:
        return list(self._reference_events.get(profile_id, []))

    def get_case(self, case_id: str) -> CaseRecord | None:
        return self._cases.get(case_id)

    def reset_demo_cases(self) -> int:
        demo_ids = [case_id for case_id, case in self._cases.items() if case.is_demo]
        for case_id in demo_ids:
            del self._cases[case_id]
        return len(demo_ids)

    def find_by_document_hash(self, document_hash: str) -> CaseRecord | None:
        return next((case for case in self._cases.values() if case.document_hash == document_hash), None)

    def list_cases(self, page: int, page_size: int, search: str | None = None, risk_level: str | None = None, document_type: str | None = None, status: str | None = None, mode: str | None = None) -> tuple[list[CaseRecord], int]:
        cases = list(self._cases.values())
        if search:
            cases = [case for case in cases if search.lower() in case.case_id.lower()]
        if risk_level:
            cases = [case for case in cases if case.risk_level == risk_level]
        if document_type:
            cases = [case for case in cases if case.document_type == document_type]
        if status:
            cases = [case for case in cases if case.screening_status == status]
        if mode == "DEMONSTRATION":
            cases = [case for case in cases if case.is_demo]
        elif mode == "NON_DEMONSTRATION":
            cases = [case for case in cases if not case.is_demo]
        cases.sort(key=lambda case: case.screening_timestamp, reverse=True)
        total = len(cases)
        start = (page - 1) * page_size
        return cases[start:start + page_size], total


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


audit_repository = AuditRepository()


def create_case_id() -> str:
    return f"CASE-{utc_now().year}-{uuid4().hex[:12].upper()}"


def history_response(case: CaseRecord) -> CaseHistoryResponse:
    return CaseHistoryResponse(
        case_id=case.case_id,
        document_type=case.document_type,
        document_hash=f"sha256:{case.document_hash}" if case.document_hash else None,
        screening_timestamp=case.screening_timestamp,
        completed_at=case.completed_at,
        screening_status=case.screening_status,
        risk_score=case.risk_score,
        risk_level=case.risk_level,
        mode="DEMONSTRATION",
        integrity_ledger="in-memory demonstration",
        modules=case.modules,
        audit_events=[AuditEventResponse(**event.__dict__) for event in case.events],
        ocr=case.details.get("ocr") if case.details else None,
        validation=case.details.get("validation") if case.details else None,
        tampering=case.details.get("tampering") if case.details else None,
        metadata=case.details.get("metadata") if case.details else None,
        face_comparison=case.details.get("face_comparison") if case.details else None,
        risk=case.details.get("risk") if case.details else None,
    )


def list_response(cases: list[CaseRecord], page: int, page_size: int, total: int) -> CaseListResponse:
    return CaseListResponse(
        items=[CaseSummaryResponse(case_id=case.case_id, document_type=case.document_type, risk_level=case.risk_level, risk_score=case.risk_score, screening_status=case.screening_status, created_at=case.screening_timestamp, completed_at=case.completed_at, mode="DEMONSTRATION", is_demo=case.is_demo) for case in cases],
        page=page,
        page_size=page_size,
        total=total,
    )


def create_audit_record(screening_id: UUID, content_hash: str, result: object) -> tuple[UUID, str]:
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"), default=str)
    record_hash = hashlib.sha256(f"{screening_id}:{content_hash}:{payload}".encode()).hexdigest()
    return uuid4(), record_hash