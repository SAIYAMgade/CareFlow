from fastapi import APIRouter, Query, status
from typing import Optional
from ..db.session import get_db
from ..services.encounter_service import EncounterService
from ..schemas.encounter import (
    EncounterCreate, EncounterResponse, EncounterListResponse,
    EncounterStatusUpdate, EncounterNotesUpdate
)

router = APIRouter(prefix="/encounters", tags=["Encounters"])

@router.get("", response_model=EncounterListResponse)
def list_encounters(
    patient_id: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    with get_db() as conn:
        svc = EncounterService(conn)
        return svc.list_encounters(patient_id=patient_id, department=department,
                                   status=status, page=page, page_size=page_size)

@router.post("", response_model=EncounterResponse, status_code=status.HTTP_201_CREATED)
def create_encounter(payload: EncounterCreate):
    with get_db() as conn:
        svc = EncounterService(conn)
        return svc.create_encounter(payload)

@router.get("/{encounter_id}", response_model=EncounterResponse)
def get_encounter(encounter_id: int):
    with get_db() as conn:
        svc = EncounterService(conn)
        return svc.get_encounter(encounter_id)

@router.put("/{encounter_id}/status", response_model=EncounterResponse)
def update_encounter_status(encounter_id: int, payload: EncounterStatusUpdate):
    with get_db() as conn:
        svc = EncounterService(conn)
        return svc.update_status(encounter_id=encounter_id, payload=payload)

@router.put("/{encounter_id}/notes", response_model=EncounterResponse)
def update_encounter_notes(encounter_id: int, payload: EncounterNotesUpdate):
    with get_db() as conn:
        svc = EncounterService(conn)
        return svc.update_notes(encounter_id=encounter_id, payload=payload)
