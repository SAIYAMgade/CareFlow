from fastapi import APIRouter, Query, status
from typing import Optional
from ..db.session import get_db
from ..services.order_service import OrderService
from ..schemas.order import OrderCreate, OrderCompleteRequest, OrderResponse, OrderListResponse
from ..schemas.result import ResultResponse

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("", response_model=OrderListResponse)
def list_orders(
    encounter_id: Optional[int] = Query(None),
    patient_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    with get_db() as conn:
        svc = OrderService(conn)
        return svc.list_orders(encounter_id=encounter_id, patient_id=patient_id,
                               status=status, priority=priority,
                               page=page, page_size=page_size)

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate):
    with get_db() as conn:
        svc = OrderService(conn)
        return svc.create_order(payload)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int):
    with get_db() as conn:
        svc = OrderService(conn)
        return svc.get_order(order_id)

@router.post("/{order_id}/complete", response_model=ResultResponse)
def complete_order_with_result(order_id: int, payload: OrderCompleteRequest):
    with get_db() as conn:
        svc = OrderService(conn)
        return svc.complete_order_with_result(order_id=order_id, payload=payload)
