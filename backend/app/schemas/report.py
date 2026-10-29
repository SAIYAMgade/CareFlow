from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ReportParameter(BaseModel):
    name: str
    label: str
    type: str # date, text, select
    default: Optional[str] = None
    options: Optional[List[str]] = None

class ReportCatalogItem(BaseModel):
    id: str
    title: str
    category: str
    description: str
    business_question: str
    parameters: List[ReportParameter]

class ReportExecutionRequest(BaseModel):
    report_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=500)

class ReportExecutionResult(BaseModel):
    report_id: str
    title: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    page: int
    page_size: int
    executed_at: str
    execution_time_ms: float
    dialect: str
