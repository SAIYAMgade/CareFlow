from fastapi import APIRouter, Query, status
from typing import Optional, Dict, Any
from ..db.session import get_db
from ..services.data_quality_service import DataQualityService
from ..schemas.data_quality import (
    DataQualityIssueResponse, DataQualityResolveRequest, DataQualityScanResult
)

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])

@router.get("/issues")
def list_issues(
    status: Optional[str] = Query(None, description="OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE"),
    severity: Optional[str] = Query(None, description="CRITICAL, HIGH, MEDIUM, LOW"),
    entity: Optional[str] = Query(None, description="APPOINTMENT, ENCOUNTER, ORDER, RESULT"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    with get_db() as conn:
        svc = DataQualityService(conn)
        return svc.list_issues(status=status, severity=severity, entity=entity, page=page, page_size=page_size)

@router.post("/scan", response_model=DataQualityScanResult)
def run_scan():
    with get_db() as conn:
        svc = DataQualityService(conn)
        return svc.run_live_audit_scan()

@router.post("/issues/{issue_id}/resolve", response_model=DataQualityIssueResponse)
def resolve_issue(issue_id: int, payload: DataQualityResolveRequest):
    with get_db() as conn:
        svc = DataQualityService(conn)
        return svc.resolve_issue(issue_id=issue_id, payload=payload)
