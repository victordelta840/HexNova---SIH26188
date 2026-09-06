from app.services.upload import sanitize_filename


def test_filename_is_safe_for_display() -> None:
    assert sanitize_filename(r"..\..\passport report!.jpg") == "passport_report_.jpg"


def test_empty_filename_gets_safe_default() -> None:
    assert sanitize_filename("") == "unnamed-document"