from fastapi import APIRouter, Query, status
from typing import Optional
from ..db.session import get_db
from ..services.order_service import OrderService
from ..schemas.result import ResultReviewRequest, ResultResponse, ResultListResponse

router = APIRouter(prefix="/results", tags=["Results"])

@router.get("", response_model=ResultListResponse)
def list_results(
    result_status: Optional[str] = Query(None, description="PENDING_REVIEW, REVIEWED"),
    abnormal_only: bool = Query(False, description="Filter only HIGH, LOW, CRITICAL"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    with get_db() as conn:
        svc = OrderService(conn)
        return svc.list_results(result_status=result_status, abnormal_only=abnormal_only,
                                page=page, page_size=page_size)

@router.post("/{result_id}/review", response_model=ResultResponse)
def review_result(result_id: int, payload: ResultReviewRequest):
    with get_db() as conn:
        svc = OrderService(conn)
        return svc.review_result(result_id=result_id, payload=payload)
