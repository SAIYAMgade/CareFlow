from fastapi import APIRouter, Query, status
from typing import Optional
from ..db.session import get_db
from ..services.patient_service import PatientService
from ..schemas.patient import PatientCreate, PatientUpdate, PatientResponse, PatientListResponse

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("", response_model=PatientListResponse)
def list_patients(
    search: Optional[str] = Query(None, description="Search by name or MRN"),
    status: Optional[str] = Query(None, description="Filter by ACTIVE, INACTIVE, MERGED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    with get_db() as conn:
        svc = PatientService(conn)
        return svc.list_patients(search=search, status=status, page=page, page_size=page_size)

@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def register_patient(payload: PatientCreate):
    with get_db() as conn:
        svc = PatientService(conn)
        return svc.register_patient(payload)

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int):
    with get_db() as conn:
        svc = PatientService(conn)
        return svc.get_patient(patient_id)

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: int, payload: PatientUpdate):
    with get_db() as conn:
        svc = PatientService(conn)
        return svc.update_patient(patient_id, payload)
