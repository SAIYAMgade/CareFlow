from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime

class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: str = Field(..., description="Format: YYYY-MM-DD")
    gender: str = Field(default="UNKNOWN", pattern="^(FEMALE|MALE|OTHER|UNKNOWN)$")
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=150)
    address: Optional[str] = Field(default=None, max_length=255)

class PatientCreate(PatientBase):
    mrn: Optional[str] = Field(default=None, description="Optional manual MRN, auto-generated if omitted")

class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=150)
    address: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, pattern="^(ACTIVE|INACTIVE|MERGED)$")

class PatientResponse(PatientBase):
    patient_id: int
    mrn: str
    status: str
    created_at: str
    updated_at: str

class PatientListResponse(BaseModel):
    items: List[PatientResponse]
    total: int
    page: int
    page_size: int
