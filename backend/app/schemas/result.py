from pydantic import BaseModel, Field
from typing import Optional, List

class ResultBase(BaseModel):
    order_id: int
    result_value: str = Field(..., max_length=100)
    reference_range: Optional[str] = Field(default=None, max_length=100)
    unit: Optional[str] = Field(default=None, max_length=30)
    abnormal_flag: str = Field(default="NORMAL", pattern="^(NORMAL|HIGH|LOW|CRITICAL)$")

class ResultReviewRequest(BaseModel):
    reviewer: str = Field(..., min_length=2, max_length=120)

class ResultResponse(ResultBase):
    result_id: int
    result_status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    result_time: str
    order_name: Optional[str] = None
    order_code: Optional[str] = None
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    department: Optional[str] = None

class ResultListResponse(BaseModel):
    items: List[ResultResponse]
    total: int
    page: int
    page_size: int
