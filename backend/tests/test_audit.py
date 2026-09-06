import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.audit import AuditRepository, create_case_id
from app.utils.hash import format_document_hash, sha256_digest
from tests.auth_helpers import AUTH_HEADERS


client = TestClient(app)
client.headers.update(AUTH_HEADERS)


def valid_png() -> io.BytesIO:
    output = io.BytesIO()
    Image.new("RGB", (16, 16), "white").save(output, format="PNG")
    output.seek(0)
    return output


def test_sha256_is_stable_and_changes_for_modified_bytes() -> None:
    original = b"synthetic-document"

    assert sha256_digest(original) == sha256_digest(original)
    assert sha256_digest(original) != sha256_digest(original + b"!")
    assert format_document_hash(sha256_digest(original)).startswith("sha256:")


def test_case_ids_are_unique_and_non_personal() -> None:
    first = create_case_id()
    second = create_case_id()

    assert first.startswith("CASE-")
    assert first != second
    assert "passport" not in first.lower()


def test_repository_records_audit_events_and_completion() -> None:
    repository = AuditRepository()
    case_id = create_case_id()
    repository.start_case(case_id, "passport")
    repository.set_document_hash(case_id, sha256_digest(b"document"))
    repository.record_event(case_id, "OCR_COMPLETED", "ocr", "COMPLETED", "OCR completed.")
    repository.complete_case(case_id, 12, "low")

    case = repository.get_case(case_id)
    assert case is not None
    assert case.screening_status == "COMPLETED"
    assert any(event.event_type == "OCR_COMPLETED" for event in case.events)


def test_integrity_endpoint_matches_and_detects_mismatch() -> None:
    data = valid_png().getvalue()
    expected = format_document_hash(sha256_digest(data))
    matching = client.post(
        "/api/v1/integrity/verify",
        data={"expected_hash": expected},
        files={"document": ("document.png", io.BytesIO(data), "image/png")},
    )
    mismatch = client.post(
        "/api/v1/integrity/verify",
        data={"expected_hash": "sha256:" + "0" * 64},
        files={"document": ("document.png", io.BytesIO(data), "image/png")},
    )

    assert matching.json()["status"] == "INTEGRITY_VERIFIED"
    assert mismatch.json()["status"] == "INTEGRITY_MISMATCH"
    assert "fraud" not in mismatch.json()["message"].lower()


def test_screening_history_api_returns_completed_case() -> None:
    response = client.post(
        "/api/v1/screening/analyze",
        data={"document_type": "passport"},
        files={"document": ("document.png", valid_png(), "image/png")},
    )
    case_id = response.json()["case_id"]

    history = client.get(f"/api/v1/cases/{case_id}")

    assert history.status_code == 200
    assert history.json()["screening_status"] == "COMPLETED"
    assert history.json()["document_hash"].startswith("sha256:")
    assert any(event["event_type"] == "SCREENING_COMPLETED" for event in history.json()["audit_events"])


def test_case_report_returns_pdf_with_case_data() -> None:
    response = client.post(
        "/api/v1/screening/analyze",
        data={"document_type": "passport"},
        files={"document": ("document.png", valid_png(), "image/png")},
    )
    case_id = response.json()["case_id"]
    report = client.get(f"/api/v1/cases/{case_id}/report")

    assert report.status_code == 200
    assert report.headers["content-type"] == "application/pdf"
    assert report.content.startswith(b"%PDF")
    assert case_id.encode() in report.content
    assert response.json()["document_hash"].encode() in report.content
    assert b"password_hash" not in report.content


def test_failed_screening_keeps_case_id_in_response_header() -> None:
    response = client.post(
        "/api/v1/screening/analyze",
        data={"document_type": "passport"},
        files={"document": ("bad.txt", io.BytesIO(b"not-a-document"), "text/plain")},
    )

    assert response.status_code == 415
    assert response.headers["x-case-id"].startswith("CASE-")