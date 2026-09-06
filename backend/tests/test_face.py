import io
import numpy as np

from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.services.face.face_detector import DetectionResult
from app.services.face import service as face_service
from tests.auth_helpers import AUTH_HEADERS


client = TestClient(app)
client.headers.update(AUTH_HEADERS)


def valid_png() -> io.BytesIO:
    output = io.BytesIO()
    Image.new("RGB", (80, 80), "white").save(output, format="PNG")
    output.seek(0)
    return output


def test_face_compare_reports_no_faces_without_inventing_match() -> None:
    response = client.post(
        "/api/v1/face/compare",
        files={
            "document": ("document.png", valid_png(), "image/png"),
            "presented_person": ("person.png", valid_png(), "image/png"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_face"]["status"] == "NO_FACE_DETECTED"
    assert payload["presented_face"]["status"] == "NO_FACE_DETECTED"
    assert payload["comparison"]["available"] is False
    assert payload["review"]["required"] is True
    assert "embedding" not in response.text.lower()


def test_face_compare_rejects_corrupt_image() -> None:
    response = client.post(
        "/api/v1/face/compare",
        files={
            "document": ("document.png", io.BytesIO(b"\x89PNG\r\n\x1a\ninvalid"), "image/png"),
            "presented_person": ("person.png", valid_png(), "image/png"),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded image is corrupted or unreadable."


def test_face_compare_rejects_unsupported_format() -> None:
    response = client.post(
        "/api/v1/face/compare",
        files={
            "document": ("document.pdf", io.BytesIO(b"%PDF-1.7"), "application/pdf"),
            "presented_person": ("person.png", valid_png(), "image/png"),
        },
    )

    assert response.status_code == 415


def test_multiple_faces_require_review_without_arbitrary_selection(monkeypatch) -> None:
    multiple = DetectionResult(status="MULTIPLE_FACES", detected=True, faces=[(0, 0, 40, 40), (40, 40, 40, 40)], quality={})
    monkeypatch.setattr(face_service, "detect_faces", lambda data: multiple)

    result = face_service.compare_face_images(b"document", b"presented")

    assert result.status == "WARNING"
    assert result.comparison["available"] is False
    assert result.presented_face.face_count == 2


def test_single_face_comparison_returns_deterministic_signal(monkeypatch) -> None:
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    texture = np.arange(60 * 60, dtype=np.uint8).reshape((60, 60))
    image[20:80, 20:80] = texture[:, :, None]
    output = io.BytesIO()
    Image.fromarray(image).save(output, format="PNG")
    image_data = output.getvalue()
    detected = DetectionResult(status="FACE_DETECTED", detected=True, faces=[(20, 20, 60, 60)], quality={})
    monkeypatch.setattr(face_service, "detect_faces", lambda data: detected)

    first = face_service.compare_face_images(image_data, image_data)
    second = face_service.compare_face_images(image_data, image_data)

    assert first.status == "REVIEW_REQUIRED"
    assert first.comparison["available"] is True
    assert first.comparison["similarity_signal"] == second.comparison["similarity_signal"]
    assert "identity" in str(first.comparison["interpretation"]).lower()