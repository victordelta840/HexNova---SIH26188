import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from tests.auth_helpers import AUTH_HEADERS


client = TestClient(app)
client.headers.update(AUTH_HEADERS)


def test_demo_scenarios_are_structured_and_complete() -> None:
    response = client.get("/api/v1/demo/scenarios")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ["demo-clean", "demo-warning", "demo-tampered"]


def test_demo_scenarios_use_the_real_screening_pipeline() -> None:
    responses = [client.post(f"/api/v1/demo/scenarios/{scenario}/run") for scenario in ["demo-clean", "demo-warning", "demo-tampered"]]

    assert all(response.status_code == 201 for response in responses)
    for response in responses:
        payload = response.json()
        assert payload["case_id"].startswith("CASE-")
        assert payload["document_hash"].startswith("sha256:")
        assert payload["ocr"]
        assert payload["validation"]
        assert payload["metadata"]
        assert payload["tampering"]
        assert payload["risk"]


def test_demo_invalid_scenario_returns_404() -> None:
    response = client.post("/api/v1/demo/scenarios/not-a-scenario/run")

    assert response.status_code == 404


def test_reset_demo_data_removes_only_demo_cases() -> None:
    client.post("/api/v1/demo/scenarios/demo-clean/run")
    response = client.post("/api/v1/demo/reset")

    assert response.status_code == 200
    assert response.json()["deleted"] >= 1
    assert client.get("/api/v1/cases", params={"mode": "DEMONSTRATION"}).json()["total"] == 0
