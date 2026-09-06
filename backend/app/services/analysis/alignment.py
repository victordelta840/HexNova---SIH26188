from __future__ import annotations

from typing import Any


def analyze_alignment(document_quality: dict[str, Any], structure_analysis: dict[str, Any] | None = None) -> dict[str, Any]:
    score = 100 - min(100, max(0, int(document_quality.get("quality_score", 75) * 0.35)))
    findings: list[str] = []

    if document_quality.get("aspect_ratio", 0) < 0.8 or document_quality.get("aspect_ratio", 0) > 2.2:
        findings.append("Document alignment is less consistent with the expected document proportions.")
        score -= 15

    if structure_analysis and structure_analysis.get("status") in {"MEDIUM_RISK", "HIGH_RISK"}:
        findings.append("Structural relationships suggest a moderate alignment discrepancy.")
        score -= 20

    if not findings:
        findings.append("Horizontal and vertical relationships are broadly consistent.")

    score = int(max(0, min(100, score)))
    if score >= 80:
        status = "PASS"
    elif score >= 60:
        status = "LOW_RISK"
    elif score >= 40:
        status = "MEDIUM_RISK"
    else:
        status = "REVIEW_REQUIRED"

    return {
        "name": "alignment_analysis",
        "status": status,
        "score": score,
        "risk_contribution": score,
        "findings": findings,
        "confidence": 0.7 if status != "REVIEW_REQUIRED" else 0.45,
        "layer": "alignment",
    }
