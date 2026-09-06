from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.face import FaceComparison


class ExtractedFieldResult(BaseModel):
    name: str
    value: str | None
    confidence: float | None
    status: Literal["unknown-unavailable", "extracted"]


class OcrResult(BaseModel):
    mode: Literal["tesseract", "unavailable", "unsupported"]
    raw_text: str
    confidence: float | None
    fields: list[ExtractedFieldResult]
    message: str


class ValidationCheck(BaseModel):
    name: str
    status: Literal["passed", "failed", "warning", "unknown-unavailable"]
    message: str


class TamperResult(BaseModel):
    mode: Literal["forensic-baseline", "unavailable", "unsupported"]
    assessment: Literal["clear", "suspicious", "unknown-unavailable"]
    risk_score: int = Field(ge=0, le=100)
    indicators: list[str]
    suspicious_regions: list[dict[str, int]]
    limitations: list[str]
    message: str


class MetadataResult(BaseModel):
    status: Literal["analyzed", "unavailable", "unsupported"]
    format: str
    width: int | None
    height: int | None
    exif_present: bool | None
    software: str | None
    findings: list[str]


class FaceResult(BaseModel):
    result: Literal["match", "possible-match", "mismatch", "unable-to-verify"]
    reason: str


class RiskResult(BaseModel):
    level: Literal["low", "medium", "high"]
    score: int = Field(ge=0, le=100)
    reasons: list[str]


class ScreeningResponse(BaseModel):
    case_id: str
    screening_id: UUID
    document_id: UUID
    document_type: str
    content_hash: str
    document_hash: str
    audit_timestamp: str
    audit_modules: list[str]
    ocr: OcrResult
    validation: list[ValidationCheck]
    tampering: TamperResult
    metadata: MetadataResult
    face_verification: FaceResult
    face_comparison: FaceComparison | None = None
    risk: RiskResult
    audit_record_hash: str
    integration_status: Literal["demonstration-mode"]

