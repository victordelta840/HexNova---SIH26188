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


def test_screening_returns_explainable_demonstration_result() -> None:
    response = client.post(
        "/api/v1/screening",
        data={"document_type": "passport"},
        files={"document": ("passport.jpg", valid_jpeg(), "image/jpeg")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["integration_status"] == "demonstration-mode"
    assert payload["ocr"]["mode"] == "unavailable"
    assert payload["face_verification"]["result"] == "unable-to-verify"
    assert payload["risk"]["reasons"]
    assert len(payload["audit_record_hash"]) == 64
    assert payload["case_id"].startswith("CASE-")
    assert payload["metadata"]["status"] == "analyzed"