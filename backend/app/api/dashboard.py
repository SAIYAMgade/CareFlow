from fastapi import APIRouter
from ..db.session import get_db
from ..services.dashboard_service import DashboardService
from ..schemas.dashboard import DashboardKpis, DashboardChartsResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardKpis)
def get_dashboard_stats():
    with get_db() as conn:
        svc = DashboardService(conn)
        return svc.get_kpis()

@router.get("/charts", response_model=DashboardChartsResponse)
def get_dashboard_charts():
    with get_db() as conn:
        svc = DashboardService(conn)
        return svc.get_charts()
