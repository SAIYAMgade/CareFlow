from pydantic import BaseModel, Field
from typing import Optional, List

class OrderBase(BaseModel):
    encounter_id: int
    patient_id: int
    order_type: str = Field(default="LABORATORY", max_length=50)
    order_code: str = Field(..., max_length=50) # CBC, BMP, LIPID, TSH, HBA1C
    order_name: str = Field(..., max_length=150)
    priority: str = Field(default="ROUTINE", pattern="^(STAT|URGENT|ROUTINE)$")
    ordered_by: str = Field(..., max_length=120)

class OrderCreate(OrderBase):
    pass

class OrderCompleteRequest(BaseModel):
    result_value: str = Field(..., max_length=100)
    reference_range: Optional[str] = Field(default=None, max_length=100)
    unit: Optional[str] = Field(default=None, max_length=30)
    abnormal_flag: str = Field(default="NORMAL", pattern="^(NORMAL|HIGH|LOW|CRITICAL)$")
    actor: str = Field(default="LAB_TECHNICIAN")

class OrderResponse(OrderBase):
    order_id: int
    order_status: str
    ordered_at: str
    completed_at: Optional[str] = None
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    department: Optional[str] = None

class OrderListResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int
