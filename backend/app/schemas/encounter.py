from pydantic import BaseModel, Field
from typing import Optional, List

class EncounterBase(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    encounter_type: str = Field(default="OUTPATIENT", max_length=50)
    department: str = Field(..., max_length=80)
    provider_name: str = Field(..., max_length=120)
    chief_complaint: Optional[str] = Field(default=None, max_length=500)
    clinical_notes: Optional[str] = None

class EncounterCreate(EncounterBase):
    pass

class EncounterStatusUpdate(BaseModel):
    new_status: str = Field(..., pattern="^(OPEN|IN_PROGRESS|AWAITING_RESULTS|COMPLETED|CANCELLED)$")
    actor: str = Field(default="ATTENDING_PHYSICIAN")
    reason: Optional[str] = Field(default=None)
    clinical_notes: Optional[str] = None

class EncounterNotesUpdate(BaseModel):
    clinical_notes: str
    actor: str = Field(default="ATTENDING_PHYSICIAN")

class EncounterResponse(EncounterBase):
    encounter_id: int
    status: str
    start_time: str
    end_time: Optional[str] = None
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    created_at: str
    updated_at: str

class EncounterListResponse(BaseModel):
    items: List[EncounterResponse]
    total: int
    page: int
    page_size: int
