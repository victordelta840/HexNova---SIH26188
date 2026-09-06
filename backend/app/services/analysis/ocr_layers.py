from __future__ import annotations

from typing import Any


def analyze_ocr(ocr_result: dict[str, Any] | None) -> dict[str, Any]:
    if not ocr_result:
        return {
            "name": "ocr_analysis",
            "status": "REVIEW_REQUIRED",
            "score": 55,
            "risk_contribution": 55,
            "findings": ["OCR was unavailable; manual verification is recommended."],
            "confidence": 0.25,
            "layer": "ocr",
        }

    confidence = ocr_result.get("confidence")
    extracted_fields = ocr_result.get("fields", [])
    missing = [field.get("name") for field in extracted_fields if field.get("status") == "unknown-unavailable"]
    score = 0
    findings: list[str] = []

    if confidence is not None:
        score = max(0, min(100, int((confidence * 100) * 0.7)))
    else:
        score = 50
    if missing:
        score += 20
        findings.append(f"Expected OCR fields were missing or not confidently extracted: {', '.join(missing[:3])}.")
    if confidence is not None and confidence < 0.6:
        findings.append("OCR confidence is below the expected screening threshold.")
        score += 20

    if not findings:
        findings.append("OCR content is structurally consistent with the expected document layout.")
    status = "PASS" if score < 25 else "LOW_RISK" if score < 45 else "MEDIUM_RISK" if score < 70 else "REVIEW_REQUIRED"
    if score >= 80:
        status = "HIGH_RISK"
    return {
        "name": "ocr_analysis",
        "status": status,
        "score": int(max(0, min(100, score))),
        "risk_contribution": int(max(0, min(100, score))),
        "findings": findings,
        "confidence": round(float(confidence or 0.5), 2),
        "layer": "ocr",
    }
