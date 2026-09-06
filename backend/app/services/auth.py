from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.schemas.auth import UserResponse


Role = Literal["OFFICER", "ADMIN"]
password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@dataclass
class UserRecord:
    user_id: str
    username: str
    email: str | None
    password_hash: str
    role: Role
    is_active: bool = True


class UserStore:
    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}

    def add_user(self, username: str, password: str, role: Role, is_active: bool = True, email: str | None = None) -> UserRecord:
        user = UserRecord(str(uuid4()), username.lower(), email.lower() if email else None, password_hash.hash(password), role, is_active)
        self._users[user.username] = user
        return user

    def seed_from_settings(self) -> None:
        settings = get_settings()
        print("\n=== STARTUP DEBUG ===")
        print(f"JWT Secret loaded: {bool(settings.jwt_secret_key)}")
        print(f"Admin pass loaded: {settings.demo_admin_password}")
        
        if not settings.jwt_secret_key:
            print("FAILED: No JWT Secret. Demo users WILL NOT be created.")
            return
            
        if settings.demo_officer_password and "demo.officer" not in self._users:
            self.add_user("demo.officer", settings.demo_officer_password, "OFFICER")
            print("SUCCESS: demo.officer created.")
        if settings.demo_admin_password and "demo.admin" not in self._users:
            self.add_user("demo.admin", settings.demo_admin_password, "ADMIN")
            print("SUCCESS: demo.admin created.")
        print("=====================\n")

    def get(self, username: str) -> UserRecord | None:
        normalized = username.lower()
        user = self._users.get(normalized)
        if user:
            return user
        return next((candidate for candidate in self._users.values() if candidate.email == normalized), None)


user_store = UserStore()
user_store.seed_from_settings()


def authenticate(username: str, password: str) -> UserRecord | None:
    print(f"\n=== LOGIN DEBUG ===")
    print(f"Attempting login for: '{username}'")
    
    user = user_store.get(username)
    if not user:
        print("FAILED: User does not exist in memory.")
        return None
        
    if not password_hash.verify(password, user.password_hash):
        print("FAILED: Password mismatch.")
        return None
        
    if not user.is_active:
        print("FAILED: User is inactive.")
        return None
        
    print("SUCCESS: Authentication passed.")
    return user


def create_access_token(user: UserRecord) -> tuple[str, int]:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured")
    expires_in = settings.access_token_expire_minutes * 60
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": user.user_id, "username": user.username, "role": user.role, "iat": now, "exp": now + timedelta(seconds=expires_in)}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserRecord:
    settings = get_settings()
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        username = payload.get("username")
        if not user_id or not username:
            raise credentials_error
    except (jwt.InvalidTokenError, RuntimeError):
        raise credentials_error from None
    user = user_store.get(username)
    if not user or user.user_id != user_id or not user.is_active:
        raise credentials_error
    return user


def require_officer(user: Annotated[UserRecord, Depends(get_current_user)]) -> UserRecord:
    return user


def require_admin(user: Annotated[UserRecord, Depends(get_current_user)]) -> UserRecord:
    if user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action.")
    return user


def user_response(user: UserRecord) -> UserResponse:
    return UserResponse(user_id=user.user_id, username=user.username, role=user.role)