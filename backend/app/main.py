from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import get_settings
from app.api.v1.documents import router as documents_router
from app.api.v1.screening import router as screening_router
from app.api.v1.face import router as face_router
from app.api.v1.integrity import router as integrity_router
from app.api.v1.cases import router as cases_router
from app.api.v1.auth import router as auth_router
from app.api.v1.reports import router as reports_router
from app.api.v1.demo import router as demo_router
from app.api.v1.reference_profiles import router as reference_profiles_router


class HealthResponse(BaseModel):
    status: str
    service: str


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://frontend-cf50fe9e3-victordelta840s-projects.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents_router, prefix=settings.api_v1_prefix)
app.include_router(screening_router, prefix=settings.api_v1_prefix)
app.include_router(face_router, prefix=settings.api_v1_prefix)
app.include_router(integrity_router, prefix=settings.api_v1_prefix)
app.include_router(cases_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(reports_router, prefix=settings.api_v1_prefix)
app.include_router(demo_router, prefix=settings.api_v1_prefix)
app.include_router(reference_profiles_router, prefix=settings.api_v1_prefix)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "The screening service could not complete the request."})


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "The request could not be validated."},
    )


@app.get(f"{settings.api_v1_prefix}/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="identity-screening-api")