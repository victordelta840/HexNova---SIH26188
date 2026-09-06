from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    user_id: str
    username: str
    role: Literal["OFFICER", "ADMIN"]


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    expires_in: int
    user: UserResponse