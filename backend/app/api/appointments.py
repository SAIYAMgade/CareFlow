from fastapi import APIRouter, Query, status
from typing import Optional
from ..db.session import get_db
from ..services.appointment_service import AppointmentService
from ..schemas.appointment import (
    AppointmentCreate, AppointmentResponse, AppointmentListResponse,
    AppointmentCheckInRequest, AppointmentCheckInResponse,
    AppointmentReschedule, AppointmentCancel
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.get("", response_model=AppointmentListResponse)
def list_appointments(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    with get_db() as conn:
        svc = AppointmentService(conn)
        return svc.list_appointments(date_str=date, department=department,
                                    status=status, patient_id=patient_id,
                                    page=page, page_size=page_size)

@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate):
    with get_db() as conn:
        svc = AppointmentService(conn)
        return svc.create_appointment(payload)

@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(appointment_id: int):
    with get_db() as conn:
        svc = AppointmentService(conn)
        return svc.get_appointment(appointment_id)

@router.post("/{appointment_id}/check-in", response_model=AppointmentCheckInResponse)
def check_in_appointment(appointment_id: int, payload: AppointmentCheckInRequest):
    with get_db() as conn:
        svc = AppointmentService(conn)
        return svc.check_in_patient(appointment_id=appointment_id, actor=payload.actor)

@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(appointment_id: int, payload: AppointmentCancel):
    with get_db() as conn:
        svc = AppointmentService(conn)
        return svc.cancel_appointment(appointment_id=appointment_id, payload=payload)

@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(appointment_id: int, payload: AppointmentReschedule):
    with get_db() as conn:
        svc = AppointmentService(conn)
        return svc.reschedule_appointment(appointment_id=appointment_id, payload=payload)
