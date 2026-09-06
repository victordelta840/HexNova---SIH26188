from app.schemas.screening import FaceResult, MetadataResult, OcrResult, RiskResult, TamperResult, ValidationCheck


def assess_risk(
    validation: list[ValidationCheck],
    tampering: TamperResult,
    face: FaceResult,
    ocr: OcrResult | None = None,
    metadata: MetadataResult | None = None,
    deep_learning_analysis: dict | None = None,
) -> RiskResult:
    score = 0
    reasons: list[str] = []
    if any(check.status == "failed" for check in validation):
        score += 50
        reasons.append("Document validation failure")
    if ocr and ocr.confidence is not None and ocr.confidence < 60:
        score += 15
        reasons.append("OCR confidence is low")
    if ocr and any(field.status == "unknown-unavailable" for field in ocr.fields):
        score += 5
        reasons.append("Required document fields were not confidently extracted")
    if tampering.assessment == "suspicious":
        score += 35
        reasons.append("Tampering indicators detected")
    elif tampering.assessment == "unknown-unavailable":
        score += 10
        reasons.append("Tampering analysis unavailable")
    if metadata and "Editing software metadata present; review required" in metadata.findings:
        score += 10
        reasons.append("Editing software metadata is present")
    if deep_learning_analysis and deep_learning_analysis.get("status") == "completed":
        deep_risk = int(deep_learning_analysis.get("risk_contribution", 0) or 0)
        if deep_risk >= 30:
            score += deep_risk
            reasons.append("Deep visual feature comparison indicates suspicious structural deviation")
        elif deep_risk > 0:
            score += deep_risk
            reasons.append("Visual similarity differs from the enrolled reference in a limited area")
    if not reasons:
        reasons.append("No negative indicators were recorded")
    level = "high" if score >= 60 else "medium" if score >= 25 else "low"
    return RiskResult(level=level, score=min(score, 100), reasons=reasons)