from __future__ import annotations

from typing import Any


def analyze_photo_structure(document_quality: dict[str, Any]) -> dict[str, Any]:
    score = int(document_quality.get("quality_score", 70))
    findings: list[str] = []

    if score < 55:
        findings.append("Photo region placement and framing are weakly supported by the available document quality signal.")
    elif score < 75:
        findings.append("Photo region appears generally consistent, but requires human review for certainty.")
    else:
        findings.append("Photo region geometry appears structurally consistent with the expected document form.")

    if score >= 80:
        status = "PASS"
    elif score >= 60:
        status = "LOW_RISK"
    elif score >= 40:
        status = "MEDIUM_RISK"
    else:
        status = "REVIEW_REQUIRED"

    return {
        "name": "photo_region_structure",
        "status": status,
        "score": score,
        "risk_contribution": score,
        "findings": findings,
        "confidence": 0.62 if score >= 60 else 0.42,
        "layer": "photo_structure",
    }
