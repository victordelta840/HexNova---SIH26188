from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.reference import ReferenceProfileCreate, ReferenceProfileResponse, ReferenceProfileUpdate
from app.services.auth import UserRecord, require_admin
from app.services.audit import audit_repository
from app.services.reference_profiles import (
    create_reference_profile_record,
    delete_reference_profile_record,
    get_reference_profile,
    list_reference_profiles,
    unlock_reference_profile_record,
    update_reference_profile_record,
)


router = APIRouter(prefix="/reference-profiles", tags=["reference-profiles"])


def _serialize_profile(profile: object, profile_id: str | None = None) -> ReferenceProfileResponse:
    if profile_id is None:
        profile_id = getattr(profile, "id", "")
    return ReferenceProfileResponse(
        id=profile.id,
        document_type=profile.document_type,
        profile_name=profile.profile_name,
        status=profile.status,
        document_hash=profile.document_hash,
        profile_summary=profile.profile_summary,
        characteristics=profile.characteristics,
        created_by=profile.created_by,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        locked_at=profile.locked_at,
        is_locked=profile.status == "LOCKED",
        last_action=profile.last_action,
        audit_events=[
            {"event_type": event.event_type, "module_name": event.module_name, "status": event.status, "timestamp": event.timestamp.isoformat(), "details": event.details}
            for event in audit_repository.get_reference_events(profile_id)
        ],
    )


@router.get("", response_model=list[ReferenceProfileResponse], dependencies=[Depends(require_admin)])
async def list_profiles(current_user: UserRecord = Depends(require_admin)) -> list[ReferenceProfileResponse]:
    return [_serialize_profile(profile, profile.id) for profile in list_reference_profiles()]


@router.post("", response_model=ReferenceProfileResponse, status_code=201, dependencies=[Depends(require_admin)])
async def create_profile(request: ReferenceProfileCreate, current_user: UserRecord = Depends(require_admin)) -> ReferenceProfileResponse:
    profile = create_reference_profile_record(
        document_type=request.document_type,
        profile_name=request.profile_name,
        document_hash=request.document_hash,
        profile_summary=request.profile_summary,
        characteristics=request.characteristics,
        created_by=current_user.username,
        authorization_code=request.authorization_code,
    )
    audit_repository.record_reference_event(profile.id, "REFERENCE_CREATED", f"Reference profile created for {request.document_type}.", current_user.user_id, current_user.role)
    return _serialize_profile(profile, profile.id)


@router.get("/{profile_id}", response_model=ReferenceProfileResponse, dependencies=[Depends(require_admin)])
async def get_profile(profile_id: str, current_user: UserRecord = Depends(require_admin)) -> ReferenceProfileResponse:
    profile = get_reference_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference profile was not found.")
    return _serialize_profile(profile, profile.id)


@router.post("/{profile_id}/replace", response_model=ReferenceProfileResponse, dependencies=[Depends(require_admin)])
async def replace_profile(profile_id: str, request: ReferenceProfileUpdate, current_user: UserRecord = Depends(require_admin)) -> ReferenceProfileResponse:
    profile = get_reference_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference profile was not found.")
    updated = update_reference_profile_record(
        profile_id=profile_id,
        profile_name=request.profile_name,
        profile_summary=request.profile_summary,
        characteristics=request.characteristics,
        authorization_code=request.authorization_code,
        current_user=current_user.username,
    )
    audit_repository.record_reference_event(profile_id, "REFERENCE_UPDATED", f"Reference profile replaced by {current_user.username}.", current_user.user_id, current_user.role)
    return _serialize_profile(updated, profile_id)


@router.post("/{profile_id}/unlock", response_model=ReferenceProfileResponse, dependencies=[Depends(require_admin)])
async def unlock_profile(profile_id: str, authorization_code: str | None = None, current_user: UserRecord = Depends(require_admin)) -> ReferenceProfileResponse:
    profile = get_reference_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference profile was not found.")
    updated = unlock_reference_profile_record(
        profile_id=profile_id,
        authorization_code=authorization_code,
        current_user=current_user.username,
    )
    audit_repository.record_reference_event(profile_id, "REFERENCE_UNLOCK_ATTEMPT", f"Reference profile unlocked by {current_user.username}.", current_user.user_id, current_user.role)
    return _serialize_profile(updated, profile_id)


@router.delete("/{profile_id}", status_code=200, dependencies=[Depends(require_admin)])
async def delete_profile(profile_id: str, authorization_code: str | None = None, current_user: UserRecord = Depends(require_admin)) -> dict[str, str]:
    delete_reference_profile_record(profile_id=profile_id, authorization_code=authorization_code, current_user=current_user.username)
    audit_repository.record_reference_event(profile_id, "REFERENCE_DELETED", f"Reference profile deleted by {current_user.username}.", current_user.user_id, current_user.role)
    return {"status": "deleted", "profile_id": profile_id}
