from fastapi import APIRouter, Query, status
from typing import Optional, List
from ..db.session import get_db
from ..repositories.observation_repo import ObservationRepository
from ..schemas.observation import ObservationCreate, ObservationResponse

router = APIRouter(prefix="/observations", tags=["Observations"])

@router.get("", response_model=List[ObservationResponse])
def list_observations(
    encounter_id: Optional[int] = Query(None),
    patient_id: Optional[int] = Query(None)
):
    with get_db() as conn:
        repo = ObservationRepository(conn)
        if encounter_id:
            raw = repo.list_by_encounter(encounter_id)
        elif patient_id:
            raw = repo.list_by_patient(patient_id)
        else:
            raw = []
        return [ObservationResponse(**r) for r in raw]

@router.post("", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
def create_observation(payload: ObservationCreate):
    with get_db() as conn:
        repo = ObservationRepository(conn)
        obs_id = repo.create(payload.model_dump())
        conn.commit()
        # Retrieve
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM OBSERVATIONS WHERE observation_id = :id", {"id": obs_id})
        from ..repositories.base import row_to_dict
        created = row_to_dict(cursor, cursor.fetchone())
        return ObservationResponse(**created)
