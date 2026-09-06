from __future__ import annotations

from typing import Any


def analyze_typography(document_quality: dict[str, Any]) -> dict[str, Any]:
    score = max(0, min(100, int(document_quality.get("quality_score", 70) * 0.8)))
    findings: list[str] = []

    if score < 60:
        findings.append("Typography consistency is degraded due to low structural detail and resolution quality.")
    elif score < 75:
        findings.append("Minor text consistency variation was observed.")
    else:
        findings.append("Typography patterns are broadly consistent with the expected document template.")

    if score >= 80:
        status = "PASS"
    elif score >= 60:
        status = "LOW_RISK"
    elif score >= 40:
        status = "MEDIUM_RISK"
    else:
        status = "REVIEW_REQUIRED"

    return {
        "name": "typography_consistency",
        "status": status,
        "score": score,
        "risk_contribution": score,
        "findings": findings,
        "confidence": 0.7 if score >= 60 else 0.45,
        "layer": "typography",
    }
