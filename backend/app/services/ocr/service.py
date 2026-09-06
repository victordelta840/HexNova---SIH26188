from app.schemas.screening import ExtractedFieldResult, OcrResult
from app.services.ocr.field_parser import parse_fields
from app.services.ocr.preprocessor import preprocess_image


def extract_fields(document_type: str, data: bytes) -> OcrResult:
    supported_fields = {
        "passport": ["name", "passport_number", "nationality", "date_of_birth", "date_of_expiry", "gender"],
        "visa": ["visa_number", "visa_type", "entry_validity", "stay_duration"],
    }.get(document_type, [])
    fields = [ExtractedFieldResult(name=name, value=None, confidence=None, status="unknown-unavailable") for name in supported_fields]
    if document_type not in ("passport", "visa"):
        return OcrResult(mode="unsupported", raw_text="", confidence=None, fields=fields, message="No OCR field profile is configured for this document type.")
    try:
        import pytesseract
        processed = preprocess_image(data)
        result = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
        words = [word for word in result["text"] if word.strip()]
        raw_text = " ".join(words)
        scores = [float(score) for score in result["conf"] if float(score) >= 0]
        confidence = sum(scores) / len(scores) if scores else None
        parsed = parse_fields(document_type, raw_text)
        fields = [ExtractedFieldResult(name=name, value=parsed.get(name), confidence=confidence, status="extracted" if name in parsed else "unknown-unavailable") for name in supported_fields]
        return OcrResult(mode="tesseract", raw_text=raw_text, confidence=confidence, fields=fields, message="OCR completed using the local Tesseract adapter.")
    except (ImportError, ModuleNotFoundError):
        return OcrResult(mode="unavailable", raw_text="", confidence=None, fields=fields, message="OCR is unavailable: install Tesseract and the Python OCR dependencies.")
    except Exception:
        return OcrResult(mode="unavailable", raw_text="", confidence=None, fields=fields, message="OCR could not read this image; no values were fabricated.")