from fastapi import APIRouter, Query
from typing import Optional
from ..db.session import get_db
from ..repositories.audit_repo import AuditRepository
from ..schemas.audit import AuditLogResponse, AuditLogListResponse

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    actor: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    with get_db() as conn:
        repo = AuditRepository(conn)
        offset = (page - 1) * page_size
        raw_items = repo.list_audit_logs(entity_type=entity_type, entity_id=entity_id,
                                         actor=actor, limit=page_size, offset=offset)
        total = repo.count_audit_logs(entity_type=entity_type, entity_id=entity_id, actor=actor)
        items = [AuditLogResponse(**r) for r in raw_items]
        return AuditLogListResponse(items=items, total=total, page=page, page_size=page_size)

@router.get("/history/{entity_type}/{entity_id}")
def get_status_history(entity_type: str, entity_id: int):
    with get_db() as conn:
        repo = AuditRepository(conn)
        return repo.list_status_history(entity_type=entity_type, entity_id=entity_id)
