from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.screening import FaceResult
from app.schemas.screening import ScreeningResponse
from app.services.audit import create_audit_record
from app.services.audit import audit_repository, create_case_id, utc_now
from app.services.face.service import compare_face_images
from app.services.metadata import analyze_metadata
from app.services.ocr.service import extract_fields
from app.services.risk import assess_risk
from app.services.tamper.service import analyze_document
from app.services.upload import validate_document_upload
from app.services.validation.service import validate_document
from app.services.auth import UserRecord, require_officer


router = APIRouter(prefix="/screening", tags=["screening"], dependencies=[Depends(require_officer)])


@router.post("", response_model=ScreeningResponse, status_code=201)
@router.post("/analyze", response_model=ScreeningResponse, status_code=201)
async def run_screening(
    document_type: Annotated[Literal["passport", "visa", "national_id", "driving_licence", "permit"], Form()],
    document: Annotated[UploadFile, File()],
    presented_person: Annotated[UploadFile | None, File()] = None,
    current_user: UserRecord = Depends(require_officer),
) -> ScreeningResponse:
    case_id = create_case_id()
    audit_repository.start_case(case_id, document_type, current_user.user_id, current_user.role)
    try:
        document_id, content_hash, _, data = await validate_document_upload(document, document_type, get_settings())
    except HTTPException as exc:
        audit_repository.fail_case(case_id, "file_validation", "File validation failed.")
        raise HTTPException(status_code=exc.status_code, detail=exc.detail, headers={**(exc.headers or {}), "X-Case-ID": case_id}) from exc
    except Exception:
        audit_repository.fail_case(case_id, "file_validation", "File validation failed.")
        raise HTTPException(status_code=500, detail="The screening service could not validate the document.", headers={"X-Case-ID": case_id}) from None
    audit_repository.set_document_hash(case_id, content_hash)
    audit_repository.record_event(case_id, "FILE_VALIDATED", "file_validation", "COMPLETED", "Original file validated and hashed.")
    screening_id = uuid4()
    ocr = extract_fields(document_type, data)
    audit_repository.record_event(case_id, "OCR_COMPLETED", "ocr", "COMPLETED", "OCR adapter completed.")
    validation = validate_document(document_type, ocr)
    audit_repository.record_event(case_id, "VALIDATION_COMPLETED", "document_validation", "COMPLETED", "Document validation checks completed.")
    tampering = analyze_document(data)
    metadata = analyze_metadata(data, document.content_type or "")
    audit_repository.record_event(case_id, "METADATA_ANALYSIS_COMPLETED", "metadata_analysis", "COMPLETED", "Metadata analysis completed.")
    audit_repository.record_event(case_id, "TAMPER_ANALYSIS_COMPLETED", "tamper_analysis", "COMPLETED", "Tamper analysis completed.")
    presented_data = None
    if presented_person is not None:
        _, _, _, presented_data = await validate_document_upload(presented_person, "passport", get_settings())
    face_comparison = compare_face_images(data, presented_data)
    audit_repository.record_event(case_id, "FACE_COMPARISON_COMPLETED", "face_comparison", "COMPLETED", "Face comparison assistance completed.")
    face = FaceResult(result="unable-to-verify", reason="Face comparison is assistive only; no automatic identity decision is made.")
    risk = assess_risk(validation, tampering, face, ocr, metadata)
    audit_repository.record_event(case_id, "RISK_ANALYSIS_COMPLETED", "risk_engine", "COMPLETED", "Risk analysis completed.")
    audit_repository.complete_case(case_id, risk.score, risk.level, {"ocr": ocr.model_dump(), "validation": [item.model_dump() for item in validation], "tampering": tampering.model_dump(), "metadata": metadata.model_dump(), "face_comparison": face_comparison.model_dump(), "risk": risk.model_dump()})
    audit_repository.record_event(case_id, "SCREENING_COMPLETED", "screening", "COMPLETED", "Screening completed.")
    audit_id, audit_hash = create_audit_record(screening_id, content_hash, risk.model_dump())
    audit_timestamp = utc_now().isoformat()
    return ScreeningResponse(
        case_id=case_id,
        screening_id=screening_id,
        document_id=document_id,
        document_type=document_type,
        content_hash=content_hash,
        document_hash=f"sha256:{content_hash}",
        audit_timestamp=audit_timestamp,
        audit_modules=["file_validation", "ocr", "document_validation", "metadata_analysis", "tamper_analysis", "face_comparison", "risk_engine"],
        ocr=ocr,
        validation=validation,
        tampering=tampering,
        metadata=metadata,
        face_verification=face,
        face_comparison=face_comparison,
        risk=risk,
        audit_record_hash=audit_hash,
        integration_status="demonstration-mode",
    )