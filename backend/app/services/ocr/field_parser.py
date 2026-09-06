import re


def parse_fields(document_type: str, text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    if document_type == "passport":
        passport = re.search(r"\b[A-Z][0-9]{7,8}\b", text.upper())
        dates = re.findall(r"\b(?:[0-3]?\d)[/-](?:[0-1]?\d)[/-](?:19|20)\d{2}\b", text)
        if passport:
            fields["passport_number"] = passport.group(0)
        if dates:
            fields["dates_detected"] = ", ".join(dates)
    elif document_type == "visa":
        visa = re.search(r"\b[A-Z0-9][A-Z0-9-]{5,15}\b", text.upper())
        if visa:
            fields["visa_number"] = visa.group(0)
    return fields