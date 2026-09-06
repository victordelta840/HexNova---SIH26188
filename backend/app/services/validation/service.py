from datetime import date, datetime

from app.schemas.screening import OcrResult, ValidationCheck


def validate_document(document_type: str, ocr: OcrResult) -> list[ValidationCheck]:
    values = {field.name: field.value for field in ocr.fields}
    required = {"passport": ["passport_number", "date_of_birth", "date_of_expiry"], "visa": ["visa_number"]}.get(document_type, [])
    missing = [name for name in required if not values.get(name)]
    checks = [ValidationCheck(name="required-fields", status="warning" if missing else "passed", message=f"Missing fields: {', '.join(missing)}." if missing else "All baseline required fields were detected.")]
    checks.append(ValidationCheck(name="document-format", status="unknown-unavailable", message="Official document rules are not configured."))
    expiry = _parse_date(values.get("date_of_expiry"))
    if values.get("date_of_expiry") and not expiry:
        checks.append(ValidationCheck(name="expiry-date-format", status="failed", message="Expiry date format could not be recognized."))
    elif expiry and expiry < date.today():
        checks.append(ValidationCheck(name="document-expiry", status="failed", message="Document expiry date has passed."))
    else:
        checks.append(ValidationCheck(name="document-expiry", status="unknown-unavailable", message="Expiry date was not confidently extracted."))
    checks.append(ValidationCheck(name="date-relationships", status="unknown-unavailable", message="Date relationships require confidently extracted dates."))
    return checks


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for pattern in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    return None