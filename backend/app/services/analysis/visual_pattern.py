from __future__ import annotations

from typing import Any


def analyze_visual_pattern(document_quality: dict[str, Any]) -> dict[str, Any]:
    score = int(document_quality.get("quality_score", 70))
    findings: list[str] = []

    if score < 50:
        findings.append("Visual anomaly or structural inconsistency detected; additional verification recommended.")
    elif score < 70:
        findings.append("Minor visual inconsistency is possible but not definitive.")
    else:
        findings.append("No significant visual pattern anomaly is evident at the current signal level.")

    if score >= 80:
        status = "PASS"
    elif score >= 60:
        status = "LOW_RISK"
    elif score >= 40:
        status = "MEDIUM_RISK"
    else:
        status = "REVIEW_REQUIRED"

    return {
        "name": "visual_pattern_analysis",
        "status": status,
        "score": score,
        "risk_contribution": score,
        "findings": findings,
        "confidence": 0.7 if score >= 60 else 0.45,
        "layer": "visual_pattern",
    }
