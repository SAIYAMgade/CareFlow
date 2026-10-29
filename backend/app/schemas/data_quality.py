from pydantic import BaseModel, Field
from typing import Optional, List

class DataQualityIssueResponse(BaseModel):
    issue_id: int
    rule_code: str
    severity: str
    affected_entity: str
    entity_id: int
    detection_time: str
    description: str
    investigation_steps: str
    resolution_status: str
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    remediation_notes: Optional[str] = None

class DataQualityResolveRequest(BaseModel):
    resolved_by: str = Field(..., min_length=2, max_length=120)
    resolution_status: str = Field(default="RESOLVED", pattern="^(RESOLVED|FALSE_POSITIVE)$")
    remediation_notes: str = Field(..., min_length=5, max_length=1000)

class DataQualityScanResult(BaseModel):
    scanned_rules_count: int
    new_issues_found: int
    open_issues_total: int
    scanned_at: str
