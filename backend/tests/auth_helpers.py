from app.core.config import get_settings
from app.services.auth import create_access_token, user_store


settings = get_settings()
settings.jwt_secret_key = "test-only-secret-key-with-sufficient-length"
user = user_store.get("test.officer") or user_store.add_user("test.officer", "test-password", "OFFICER")
_token, _ = create_access_token(user)
AUTH_HEADERS = {"Authorization": f"Bearer {_token}"}
