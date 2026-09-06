from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.services.auth import authenticate, create_access_token, get_current_user, user_response


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    user = authenticate(request.username, request.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.", headers={"WWW-Authenticate": "Bearer"})
    try:
        token, expires_in = create_access_token(user)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Authentication is not configured.") from None
    return LoginResponse(access_token=token, token_type="bearer", expires_in=expires_in, user=user_response(user))


@router.get("/me", response_model=UserResponse)
async def current_user(user=Depends(get_current_user)) -> UserResponse:
    return user_response(user)