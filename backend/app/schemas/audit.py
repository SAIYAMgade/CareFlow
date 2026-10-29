from pydantic import BaseModel
from typing import Optional, List

class AuditLogResponse(BaseModel):
    audit_id: int
    entity_type: str
    entity_id: int
    action: str
    actor: str
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    correlation_id: Optional[str] = None
    reason: Optional[str] = None
    changed_at: str

class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
