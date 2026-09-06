from app.schemas.screening import ExtractedFieldResult, OcrResult
from app.services.validation.service import validate_document


def ocr_with_expiry(value: str) -> OcrResult:
    return OcrResult(
        mode="tesseract",
        raw_text=value,
        confidence=90,
        fields=[
            ExtractedFieldResult(name="passport_number", value="A1234567", confidence=90, status="extracted"),
            ExtractedFieldResult(name="date_of_birth", value="01/01/1990", confidence=90, status="extracted"),
            ExtractedFieldResult(name="date_of_expiry", value=value, confidence=90, status="extracted"),
        ],
        message="Synthetic test OCR",
    )


def test_expired_document_fails_expiry_check() -> None:
    checks = validate_document("passport", ocr_with_expiry("01/01/2020"))

    expiry = next(check for check in checks if check.name == "document-expiry")
    assert expiry.status == "failed"


def test_invalid_expiry_is_reported_as_failure() -> None:
    checks = validate_document("passport", ocr_with_expiry("not-a-date"))

    expiry = next(check for check in checks if check.name == "expiry-date-format")
    assert expiry.status == "failed"