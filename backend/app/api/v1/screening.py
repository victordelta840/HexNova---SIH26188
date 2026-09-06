from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.screening import FaceResult
from app.schemas.screening import ScreeningResponse
from app.services.audit import create_audit_record
from app.services.audit import audit_repository, create_case_id, utc_now
from app.services.face.service import compare_face_images
from app.services.analysis.alignment import analyze_alignment
from app.services.analysis.ocr_layers import analyze_ocr
from app.services.analysis.photo_structure import analyze_photo_structure
from app.services.analysis.preprocessing import preprocess_document
from app.services.analysis.reference_comparison import analyze_reference_comparison
from app.services.analysis.structure import analyze_structure
from app.services.analysis.typography import analyze_typography
from app.services.analysis.visual_pattern import analyze_visual_pattern
from app.services.deep_learning.service import analyze_deep_learning_document
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
    document_quality = preprocess_document(data, document.content_type or "")
    structure_analysis = analyze_structure(document_quality)
    ocr_analysis = analyze_ocr(ocr.model_dump() if ocr else None)
    alignment_analysis = analyze_alignment(document_quality, structure_analysis)
    typography_analysis = analyze_typography(document_quality)
    photo_region_analysis = analyze_photo_structure(document_quality)
    visual_pattern_analysis = analyze_visual_pattern(document_quality)
    reference_profile_analysis = analyze_reference_comparison(document_quality)
    deep_learning_analysis = analyze_deep_learning_document(data, document_type=document_type)
    audit_repository.record_event(case_id, "METADATA_ANALYSIS_COMPLETED", "metadata_analysis", "COMPLETED", "Metadata analysis completed.")
    audit_repository.record_event(case_id, "TAMPER_ANALYSIS_COMPLETED", "tamper_analysis", "COMPLETED", "Tamper analysis completed.")
    presented_data = None
    if presented_person is not None:
        _, _, _, presented_data = await validate_document_upload(presented_person, "passport", get_settings())
    face_comparison = compare_face_images(data, presented_data)
    audit_repository.record_event(case_id, "FACE_COMPARISON_COMPLETED", "face_comparison", "COMPLETED", "Face comparison assistance completed.")
    face = FaceResult(result="unable-to-verify", reason="Face comparison is assistive only; no automatic identity decision is made.")
    risk = assess_risk(validation, tampering, face, ocr, metadata, deep_learning_analysis)
    audit_repository.record_event(case_id, "RISK_ANALYSIS_COMPLETED", "risk_engine", "COMPLETED", "Risk analysis completed.")
    audit_repository.complete_case(case_id, risk.score, risk.level, {"ocr": ocr.model_dump(), "validation": [item.model_dump() for item in validation], "tampering": tampering.model_dump(), "metadata": metadata.model_dump(), "face_comparison": face_comparison.model_dump(), "risk": risk.model_dump(), "document_quality": document_quality, "structure_analysis": structure_analysis, "ocr_analysis": ocr_analysis, "alignment_analysis": alignment_analysis, "typography_analysis": typography_analysis, "photo_region_analysis": photo_region_analysis, "visual_pattern_analysis": visual_pattern_analysis, "reference_profile_analysis": reference_profile_analysis, "deep_learning_analysis": deep_learning_analysis})
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
        risk={
            **risk.model_dump(),
            "recommended_action": "MANUAL_REVIEW_RECOMMENDED" if risk.score >= 25 else "APPROVED_FOR_FURTHER_PROCESSING",
            "confidence": 0.72,
        },
        audit_record_hash=audit_hash,
        integration_status="demonstration-mode",
        document_quality={
            "name": "document_quality",
            "status": document_quality["status"],
            "score": int(document_quality["quality_score"]),
            "risk_contribution": int(document_quality["quality_score"]),
            "findings": document_quality["findings"],
            "confidence": document_quality["confidence"],
            "layer": "document_quality",
        },
        structure_analysis={
            "name": "structure_analysis",
            "status": structure_analysis["status"],
            "score": int(structure_analysis["score"]),
            "risk_contribution": int(structure_analysis["risk_contribution"]),
            "findings": structure_analysis["findings"],
            "confidence": structure_analysis["confidence"],
            "layer": "structure",
        },
        ocr_analysis={
            "name": "ocr_analysis",
            "status": ocr_analysis["status"],
            "score": int(ocr_analysis["score"]),
            "risk_contribution": int(ocr_analysis["risk_contribution"]),
            "findings": ocr_analysis["findings"],
            "confidence": ocr_analysis["confidence"],
            "layer": "ocr",
        },
        alignment_analysis={
            "name": "alignment_analysis",
            "status": alignment_analysis["status"],
            "score": int(alignment_analysis["score"]),
            "risk_contribution": int(alignment_analysis["risk_contribution"]),
            "findings": alignment_analysis["findings"],
            "confidence": alignment_analysis["confidence"],
            "layer": "alignment",
        },
        typography_analysis={
            "name": "typography_consistency",
            "status": typography_analysis["status"],
            "score": int(typography_analysis["score"]),
            "risk_contribution": int(typography_analysis["risk_contribution"]),
            "findings": typography_analysis["findings"],
            "confidence": typography_analysis["confidence"],
            "layer": "typography",
        },
        photo_region_analysis={
            "name": "photo_region_structure",
            "status": photo_region_analysis["status"],
            "score": int(photo_region_analysis["score"]),
            "risk_contribution": int(photo_region_analysis["risk_contribution"]),
            "findings": photo_region_analysis["findings"],
            "confidence": photo_region_analysis["confidence"],
            "layer": "photo_structure",
        },
        visual_pattern_analysis={
            "name": "visual_pattern_analysis",
            "status": visual_pattern_analysis["status"],
            "score": int(visual_pattern_analysis["score"]),
            "risk_contribution": int(visual_pattern_analysis["risk_contribution"]),
            "findings": visual_pattern_analysis["findings"],
            "confidence": visual_pattern_analysis["confidence"],
            "layer": "visual_pattern",
        },
        reference_profile_analysis={
            "name": "reference_profile_comparison",
            "status": reference_profile_analysis["status"],
            "score": int(reference_profile_analysis["score"]),
            "risk_contribution": int(reference_profile_analysis["risk_contribution"]),
            "findings": reference_profile_analysis["findings"],
            "confidence": reference_profile_analysis["confidence"],
            "layer": "reference_compare",
        },
        deep_learning_analysis={
            "name": "deep_learning_analysis",
            "status": "PASS" if deep_learning_analysis.get("status") == "completed" else "REVIEW_REQUIRED",
            "score": int(min(100, max(0, round((1.0 - deep_learning_analysis.get("global_similarity", 0.0)) * 100)))) if deep_learning_analysis.get("global_similarity") is not None else 0,
            "risk_contribution": int(deep_learning_analysis.get("risk_contribution", 0) or 0),
            "findings": deep_learning_analysis.get("explanations", ["Deep learning analysis unavailable."]),
            "confidence": 0.8 if deep_learning_analysis.get("status") == "completed" else 0.2,
            "layer": "deep_learning",
        },
    )