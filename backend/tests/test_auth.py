from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.core.config import get_settings
from app.main import app
from app.services.auth import authenticate, create_access_token, password_hash, require_admin, user_store


client = TestClient(app)
settings = get_settings()
settings.jwt_secret_key = "test-only-secret-key-with-sufficient-length"


def test_password_is_hashed_and_not_stored_plaintext() -> None:
    user = user_store.add_user("auth.officer", "strong-password", "OFFICER")

    assert user.password_hash != "strong-password"
    assert password_hash.verify("strong-password", user.password_hash)
    assert not password_hash.verify("wrong-password", user.password_hash)


def test_successful_officer_and_admin_login() -> None:
    officer = user_store.add_user("login.officer", "officer-password", "OFFICER")
    admin = user_store.add_user("login.admin", "admin-password", "ADMIN")

    officer_response = client.post("/api/v1/auth/login", json={"username": officer.username, "password": "officer-password"})
    admin_response = client.post("/api/v1/auth/login", json={"username": admin.username, "password": "admin-password"})

    assert officer_response.status_code == 200
    assert officer_response.json()["user"]["role"] == "OFFICER"
    assert admin_response.status_code == 200
    assert admin_response.json()["user"]["role"] == "ADMIN"
    assert "password" not in officer_response.text.lower()


def test_login_accepts_configured_email() -> None:
    user = user_store.add_user("email.login", "email-password", "OFFICER", email="reviewer@example.test")

    response = client.post("/api/v1/auth/login", json={"username": user.email, "password": "email-password"})

    assert response.status_code == 200
    assert response.json()["user"]["username"] == user.username


def test_invalid_credentials_are_generic() -> None:
    response = client.post("/api/v1/auth/login", json={"username": "missing-user", "password": "wrong"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password."}


def test_expired_and_invalid_tokens_are_rejected() -> None:
    expired = jwt.encode({"sub": "user", "username": "nobody", "role": "OFFICER", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    invalid = "not.a.valid.token"

    expired_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    invalid_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {invalid}"})

    assert expired_response.status_code == 401
    assert invalid_response.status_code == 401


def test_missing_token_is_rejected_for_protected_endpoint() -> None:
    response = TestClient(app).get("/api/v1/cases")

    assert response.status_code == 401


def test_inactive_user_cannot_authenticate() -> None:
    user = user_store.add_user("inactive.user", "inactive-password", "OFFICER", is_active=False)

    assert authenticate(user.username, "inactive-password") is None
    response = client.post("/api/v1/auth/login", json={"username": user.username, "password": "inactive-password"})
    assert response.status_code == 401


def test_admin_guard_rejects_officer_and_accepts_admin() -> None:
    officer = user_store.add_user("guard.officer", "officer-password", "OFFICER")
    admin = user_store.add_user("guard.admin", "admin-password", "ADMIN")

    with pytest.raises(HTTPException) as error:
        require_admin(officer)

    assert error.value.status_code == 403
    assert require_admin(admin) is admin


def test_current_user_endpoint_validates_token() -> None:
    user = user_store.add_user("me.officer", "me-password", "OFFICER")
    token, _ = create_access_token(user)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"user_id": user.user_id, "username": user.username, "role": "OFFICER"}
