from pydantic import BaseModel, Field
from typing import Optional, List

class ObservationBase(BaseModel):
    encounter_id: int
    patient_id: int
    observation_type: str = Field(..., max_length=50) # e.g. VITAL_SIGNS
    observation_code: str = Field(..., max_length=30) # e.g. BP_SYS, HEART_RATE, TEMP
    value_numeric: Optional[float] = None
    value_text: Optional[str] = Field(default=None, max_length=255)
    unit: Optional[str] = Field(default=None, max_length=30)
    source: str = Field(default="CLINICAL_TRIAGE", max_length=50)

class ObservationCreate(ObservationBase):
    pass

class ObservationResponse(ObservationBase):
    observation_id: int
    observation_time: str
    status: str
