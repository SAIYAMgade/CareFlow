from pydantic import BaseModel, Field
from typing import Optional, List

class AppointmentBase(BaseModel):
    patient_id: int
    appointment_time: str = Field(..., description="ISO 8601 Timestamp, e.g. 2026-10-29T10:00:00")
    appointment_type: str = Field(default="FOLLOW_UP", max_length=50)
    department: str = Field(..., max_length=80)
    provider_name: str = Field(..., max_length=120)

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentReschedule(BaseModel):
    new_appointment_time: str
    actor: str = Field(default="CLINIC_STAFF")
    reason: Optional[str] = Field(default="Patient requested reschedule")

class AppointmentCancel(BaseModel):
    cancel_reason: str = Field(..., min_length=2, max_length=255)
    actor: str = Field(default="CLINIC_STAFF")

class AppointmentCheckInRequest(BaseModel):
    actor: str = Field(default="FRONT_DESK")

class AppointmentCheckInResponse(BaseModel):
    appointment_id: int
    status: str
    check_in_time: str
    encounter_id: int
    message: str

class AppointmentResponse(AppointmentBase):
    appointment_id: int
    status: str
    check_in_time: Optional[str] = None
    cancel_reason: Optional[str] = None
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    created_at: str
    updated_at: str

class AppointmentListResponse(BaseModel):
    items: List[AppointmentResponse]
    total: int
    page: int
    page_size: int
