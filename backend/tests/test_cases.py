import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from tests.auth_helpers import AUTH_HEADERS


client = TestClient(app)
client.headers.update(AUTH_HEADERS)


def valid_png() -> io.BytesIO:
    output = io.BytesIO()
    Image.new("RGB", (16, 16), "white").save(output, format="PNG")
    output.seek(0)
    return output


def create_case(document_type: str = "passport") -> str:
    response = client.post(
        "/api/v1/screening/analyze",
        data={"document_type": document_type},
        files={"document": (f"{document_type}.png", valid_png(), "image/png")},
    )
    assert response.status_code == 201
    return response.json()["case_id"]


def test_case_list_supports_search_filter_and_pagination() -> None:
    case_id = create_case()
    create_case("visa")

    searched = client.get("/api/v1/cases", params={"search": case_id, "page": 1, "page_size": 1})
    filtered = client.get("/api/v1/cases", params={"document_type": "visa"})

    assert searched.status_code == 200
    assert searched.json()["total"] == 1
    assert searched.json()["items"][0]["case_id"] == case_id
    assert filtered.json()["total"] >= 1
    assert all(item["document_type"] == "visa" for item in filtered.json()["items"])


def test_case_list_rejects_invalid_filters_and_case_returns_404() -> None:
    invalid = client.get("/api/v1/cases", params={"risk_level": "CRITICAL"})
    missing = client.get("/api/v1/cases/CASE-2026-NOT-FOUND")

    assert invalid.status_code == 422
    assert missing.status_code == 404