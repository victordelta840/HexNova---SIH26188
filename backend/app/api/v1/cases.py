from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.audit import CaseHistoryResponse, CaseListResponse
from app.services.audit import audit_repository, history_response, list_response
from app.services.auth import UserRecord, require_officer


router = APIRouter(prefix="/cases", tags=["audit"], dependencies=[Depends(require_officer)])


@router.get("", response_model=CaseListResponse)
async def list_case_history(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=64)] = None,
    risk_level: Annotated[Literal["LOW", "MEDIUM", "HIGH"] | None, Query()] = None,
    document_type: Annotated[str | None, Query(max_length=32)] = None,
    status: Annotated[Literal["PROCESSING", "COMPLETED", "FAILED", "REVIEW_REQUIRED"] | None, Query()] = None,
    mode: Annotated[Literal["DEMONSTRATION", "NON_DEMONSTRATION"] | None, Query()] = None,
) -> CaseListResponse:
    cases, total = audit_repository.list_cases(page, page_size, search, risk_level.lower() if risk_level else None, document_type, status, mode)
    return list_response(cases, page, page_size, total)


@router.get("/{case_id}", response_model=CaseHistoryResponse)
async def get_case_history(case_id: str, current_user: UserRecord = Depends(require_officer)) -> CaseHistoryResponse:
    case = audit_repository.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Screening case was not found.")
    audit_repository.record_event(case_id, "CASE_VIEWED", "case_management", "COMPLETED", "Case details viewed.", current_user.user_id, current_user.role)
    return history_response(case)