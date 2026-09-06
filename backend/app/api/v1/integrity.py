from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.config import get_settings
from app.schemas.audit import IntegrityVerificationResponse
from app.services.upload import validate_document_upload
from app.utils.hash import format_document_hash
from app.services.auth import UserRecord, require_officer
from app.services.audit import audit_repository


router = APIRouter(prefix="/integrity", tags=["integrity"], dependencies=[Depends(require_officer)])


@router.post("/verify", response_model=IntegrityVerificationResponse)
async def verify_integrity(
    document: Annotated[UploadFile, File()],
    expected_hash: Annotated[str | None, Form()] = None,
    current_user: UserRecord = Depends(require_officer),
) -> IntegrityVerificationResponse:
    _, digest, _, _ = await validate_document_upload(document, "passport", get_settings())
    current_hash = format_document_hash(digest)
    normalized_expected = expected_hash.strip().lower() if expected_hash else None
    if normalized_expected and not normalized_expected.startswith("sha256:"):
        normalized_expected = format_document_hash(normalized_expected)
    match = normalized_expected is None or current_hash == normalized_expected
    audit_case = audit_repository.find_by_document_hash(digest)
    if audit_case:
        audit_repository.record_event(audit_case.case_id, "INTEGRITY_VERIFIED" if match else "INTEGRITY_MISMATCH", "integrity", "COMPLETED", "Integrity comparison completed.", current_user.user_id, current_user.role)
    return IntegrityVerificationResponse(
        match=match,
        current_hash=current_hash,
        expected_hash=normalized_expected,
        status="INTEGRITY_VERIFIED" if match else "INTEGRITY_MISMATCH",
        message="Integrity verified for the supplied bytes." if match else "File integrity mismatch detected. Authorized human review is required.",
    )