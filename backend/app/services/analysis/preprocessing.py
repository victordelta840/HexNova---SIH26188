from __future__ import annotations

from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError


def preprocess_document(data: bytes, content_type: str) -> dict[str, Any]:
    """Return practical document-quality signals without inventing evidence."""
    try:
        image = Image.open(BytesIO(data))
        image.load()
        width, height = image.size
        aspect_ratio = width / height if height else 0.0
        rotation = "upright"
        if width > height * 1.25:
            rotation = "landscape"
        elif height > width * 1.25:
            rotation = "portrait"

        quality_score = min(100, max(0, int((min(width, height) / max(width, height)) * 100)))
        if width < 400 or height < 300:
            quality_score = max(0, quality_score - 15)

        findings: list[str] = []
        if quality_score < 50:
            findings.append("Low structural detail density")
        if aspect_ratio < 0.8 or aspect_ratio > 2.2:
            findings.append("Aspect ratio is outside the expected document profile range")

        status = "PASS"
        if quality_score < 55 or findings:
            status = "LOW_RISK" if quality_score >= 40 else "REVIEW_REQUIRED"

        return {
            "status": status,
            "score": quality_score,
            "quality_score": quality_score,
            "format": image.format or content_type.split("/")[-1].upper(),
            "width": width,
            "height": height,
            "aspect_ratio": round(aspect_ratio, 4),
            "orientation": rotation,
            "findings": findings,
            "confidence": 0.82 if quality_score >= 60 else 0.65,
            "metadata": {"source": "image_preprocessing"},
        }
    except (UnidentifiedImageError, OSError, ValueError):
        return {
            "status": "REVIEW_REQUIRED",
            "score": 25,
            "quality_score": 25,
            "format": content_type.split("/")[-1].upper() if "/" in content_type else "UNKNOWN",
            "width": None,
            "height": None,
            "aspect_ratio": 0.0,
            "orientation": "unknown",
            "findings": ["Document could not be processed reliably for quality analysis."],
            "confidence": 0.25,
            "metadata": {"source": "image_preprocessing"},
        }
