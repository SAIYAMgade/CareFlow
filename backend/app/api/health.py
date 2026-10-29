from fastapi import APIRouter
from typing import Dict, Any
from ..db.session import check_db_health
from ..core.config import settings

router = APIRouter(prefix="/health", tags=["System Health"])

@router.get("")
def get_system_health() -> Dict[str, Any]:
    db_status = check_db_health()
    overall_status = "UP" if db_status.get("connected") else "DEGRADED"
    return {
        "status": overall_status,
        "application": "CareFlow Healthcare Operations Platform",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT_NAME,
        "database": db_status
    }
