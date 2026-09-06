from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette.datastructures import Headers
from starlette.datastructures import UploadFile

from app.schemas.demo import DemoScenario, SCENARIOS
from app.schemas.screening import ScreeningResponse
from app.services.audit import audit_repository
from app.services.auth import UserRecord, require_officer
from app.api.v1.screening import run_screening


router = APIRouter(prefix="/demo", tags=["demonstration"])


def synthetic_document(scenario_id: str) -> bytes:
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (900, 560), "white")
    draw = ImageDraw.Draw(image)
    draw.text((35, 30), "SYNTHETIC TEST DOCUMENT - NOT VALID FOR TRAVEL OR IDENTIFICATION", fill="black")
    draw.text((35, 100), "ALEX DEMO", fill="black")
    draw.text((35, 145), "PASSPORT NO: DEMO000001   NATIONALITY: TEST", fill="black")
    draw.text((35, 190), "DATE OF BIRTH: 01/01/1990", fill="black")
    draw.text((35, 235), "DATE OF EXPIRY: 01/01/2035", fill="black")
    if scenario_id == "demo-warning":
        draw.rectangle((650, 120, 850, 420), fill=(245, 245, 245))
    if scenario_id == "demo-tampered":
        draw.rectangle((500, 270, 850, 500), fill=(20, 20, 20))
        draw.text((520, 300), "CONTROLLED ALTERATION", fill="white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


@router.get("/scenarios", response_model=list[DemoScenario])
async def list_demo_scenarios(_: Annotated[UserRecord, Depends(require_officer)]) -> list[DemoScenario]:
    return SCENARIOS


@router.post("/scenarios/{scenario_id}/run", response_model=ScreeningResponse, status_code=201)
async def run_demo(scenario_id: str, current_user: Annotated[UserRecord, Depends(require_officer)]) -> ScreeningResponse:
    scenario = next((item for item in SCENARIOS if item.id == scenario_id), None)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Demonstration scenario was not found.")
    upload = UploadFile(file=BytesIO(synthetic_document(scenario_id)), filename=f"{scenario_id}.png", headers=Headers({"content-type": "image/png"}))
    response = await run_screening(scenario.document_type, upload, None, current_user)
    case = audit_repository.get_case(response.case_id)
    if case:
        case.is_demo = True
        case.details["demo_scenario"] = scenario.model_dump() if case.details else scenario.model_dump()
    return response


@router.post("/reset")
async def reset_demo(_: Annotated[UserRecord, Depends(require_officer)]) -> dict[str, int | str]:
    return {"deleted": audit_repository.reset_demo_cases(), "status": "DEMO_DATA_RESET"}