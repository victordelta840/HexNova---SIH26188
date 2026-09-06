from __future__ import annotations

from typing import Any


def analyze_reference_comparison(document_quality: dict[str, Any], reference_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    score = int(document_quality.get("quality_score", 70))
    findings: list[str] = []

    if reference_profile:
        ref_summary = reference_profile.get("profile_summary", {})
        ratio = ref_summary.get("aspect_ratio")
        if ratio is not None and abs(ratio - document_quality.get("aspect_ratio", ratio)) > 0.18:
            findings.append("The uploaded document deviates notably from the locked reference profile geometry.")
            score -= 15
        else:
            findings.append("The uploaded document remains broadly aligned with the locked reference structure.")
    else:
        findings.append("No authorized reference profile is active for comparison; risk is based on the available signal set.")
        score -= 10

    if score >= 80:
        status = "PASS"
    elif score >= 60:
        status = "LOW_RISK"
    elif score >= 40:
        status = "MEDIUM_RISK"
    else:
        status = "REVIEW_REQUIRED"

    return {
        "name": "reference_profile_comparison",
        "status": status,
        "score": max(0, min(100, score)),
        "risk_contribution": max(0, min(100, score)),
        "findings": findings,
        "confidence": 0.78 if score >= 60 else 0.48,
        "layer": "reference_compare",
    }
