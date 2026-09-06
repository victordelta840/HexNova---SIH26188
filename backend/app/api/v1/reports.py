from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.services.audit import audit_repository
from app.services.auth import UserRecord, require_officer
from app.services.report import build_screening_report


router = APIRouter(prefix="/cases", tags=["reports"], dependencies=[Depends(require_officer)])


@router.get("/{case_id}/report")
async def download_case_report(case_id: str, current_user: Annotated[UserRecord, Depends(require_officer)]) -> Response:
    case = audit_repository.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Screening case was not found.")
    audit_repository.record_event(case_id, "REPORT_GENERATED", "reporting", "COMPLETED", "Screening report generated.", current_user.user_id, current_user.role)
    pdf = build_screening_report(case)
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{case.case_id}-screening-report.pdf"'})
