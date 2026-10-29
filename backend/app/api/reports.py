from fastapi import APIRouter, Response, Query
from typing import List, Dict, Any
from ..db.session import get_db
from ..services.report_service import ReportService
from ..schemas.report import ReportCatalogItem, ReportExecutionRequest, ReportExecutionResult

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/catalog", response_model=List[ReportCatalogItem])
def get_report_catalog():
    with get_db() as conn:
        svc = ReportService(conn)
        return svc.get_catalog()

@router.post("/execute", response_model=ReportExecutionResult)
def execute_report(payload: ReportExecutionRequest):
    with get_db() as conn:
        svc = ReportService(conn)
        return svc.execute_report(
            report_id=payload.report_id,
            params=payload.parameters,
            page=payload.page,
            page_size=payload.page_size
        )

@router.post("/export")
def export_report_csv(payload: ReportExecutionRequest):
    with get_db() as conn:
        svc = ReportService(conn)
        csv_content = svc.export_csv(report_id=payload.report_id, params=payload.parameters)
        filename = f"{payload.report_id.lower()}_export.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
