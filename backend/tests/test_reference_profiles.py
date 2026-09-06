from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services.auth import create_access_token, user_store

client = TestClient(app)


def _auth_headers_for(username: str, password: str):
    user = user_store.get(username) or user_store.add_user(username, password, "OFFICER")
    token, _ = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


def _admin_headers():
    user = user_store.get("test.admin") or user_store.add_user("test.admin", "admin-password", "ADMIN")
    token, _ = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


def test_reference_profile_creation_requires_admin_and_secret() -> None:
    settings = get_settings()
    settings.reference_profile_lock_secret = "demo-admin-secret"

    response = client.post(
        "/api/v1/reference-profiles",
        json={
            "document_type": "passport",
            "profile_name": "passport-demo-profile",
            "document_hash": "sha256:abc123",
            "profile_summary": {"aspect_ratio": 1.4, "layout_consistency": 95},
            "characteristics": {"major_regions": 6, "photo_region": {"x": 112, "y": 224}},
            "authorization_code": "demo-admin-secret",
        },
        headers=_admin_headers(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "LOCKED"
    assert payload["profile_name"] == "passport-demo-profile"
    assert payload["is_locked"] is True


def test_reference_profile_lock_prevents_replace_without_secret() -> None:
    settings = get_settings()
    settings.reference_profile_lock_secret = "demo-admin-secret"

    create_response = client.post(
        "/api/v1/reference-profiles",
        json={
            "document_type": "passport",
            "profile_name": "passport-lock-test",
            "document_hash": "sha256:lock-test",
            "profile_summary": {"aspect_ratio": 1.4},
            "characteristics": {"major_regions": 5},
            "authorization_code": "demo-admin-secret",
        },
        headers=_admin_headers(),
    )
    profile_id = create_response.json()["id"]

    replace_response = client.post(
        f"/api/v1/reference-profiles/{profile_id}/replace",
        json={
            "profile_name": "passport-lock-test-updated",
            "profile_summary": {"aspect_ratio": 1.5},
            "characteristics": {"major_regions": 6},
            "authorization_code": "wrong-secret",
        },
        headers=_admin_headers(),
    )

    assert replace_response.status_code == 403
    payload = replace_response.json()
    assert "locked" in payload["detail"].lower() or "secret" in payload["detail"].lower()
