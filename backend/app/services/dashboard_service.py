from typing import Dict, Any
from ..repositories.dashboard_repo import DashboardRepository
from ..schemas.dashboard import DashboardKpis, DashboardChartsResponse

class DashboardService:
    def __init__(self, conn):
        self.conn = conn
        self.repo = DashboardRepository(conn)

    def get_kpis(self) -> DashboardKpis:
        kpi_data = self.repo.get_kpis()
        return DashboardKpis(**kpi_data)

    def get_charts(self) -> DashboardChartsResponse:
        charts_data = self.repo.get_charts()
        return DashboardChartsResponse(**charts_data)
