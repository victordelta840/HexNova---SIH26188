import io
from PIL import Image

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_helpers import AUTH_HEADERS


client = TestClient(app)
client.headers.update(AUTH_HEADERS)


def valid_jpeg() -> io.BytesIO:
    output = io.BytesIO()
    Image.new("RGB", (32, 32), "white").save(output, format="JPEG")
    output.seek(0)
    return output


def test_upload_accepts_supported_image_and_returns_hash() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        data={"document_type": "passport"},
        files={"document": ("passport.jpg", valid_jpeg(), "image/jpeg")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "accepted"
    assert len(payload["content_hash"]) == 64
    assert payload["size_bytes"] > 7


def test_upload_rejects_mismatched_content() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        data={"document_type": "passport"},
        files={"document": ("passport.jpg", io.BytesIO(b"not-an-image"), "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "The document content does not match its format."}


def test_upload_rejects_corrupt_image_with_valid_signature() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        data={"document_type": "passport"},
        files={"document": ("passport.jpg", io.BytesIO(b"\xff\xd8\xffcorrupt"), "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "The uploaded image is corrupted or unreadable."}