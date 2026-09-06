from __future__ import annotations

from typing import Any


def analyze_structure(document_quality: dict[str, Any], reference_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    score = document_quality.get("score", 50)
    findings: list[str] = []

    if document_quality.get("aspect_ratio", 0) < 0.8 or document_quality.get("aspect_ratio", 0) > 2.2:
        findings.append("Major aspect ratio deviates from expected document profile.")
        score = min(100, score + 18)

    if reference_profile:
        reference_ratio = reference_profile.get("profile_summary", {}).get("aspect_ratio")
        if reference_ratio and abs(reference_ratio - document_quality.get("aspect_ratio", reference_ratio)) > 0.25:
            findings.append("Document structure does not align closely with the locked reference profile.")
            score = min(100, score + 22)

    if not findings:
        status = "PASS"
    elif score >= 70:
        status = "HIGH_RISK"
    elif score >= 45:
        status = "MEDIUM_RISK"
    else:
        status = "LOW_RISK"

    return {
        "name": "structure_analysis",
        "status": status,
        "score": int(max(0, min(score, 100))),
        "risk_contribution": int(max(0, min(score, 100))),
        "findings": findings or ["Document structure is broadly consistent with the expected document geometry."],
        "confidence": 0.8 if not findings else 0.65,
        "layer": "structure",
    }
