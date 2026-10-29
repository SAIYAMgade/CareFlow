from datetime import datetime
from typing import Optional, Dict, Any, List
from ..repositories.order_repo import OrderRepository
from ..repositories.result_repo import ResultRepository
from ..repositories.encounter_repo import EncounterRepository
from ..repositories.patient_repo import PatientRepository
from ..repositories.audit_repo import AuditRepository
from ..schemas.order import OrderCreate, OrderCompleteRequest, OrderResponse, OrderListResponse
from ..schemas.result import ResultReviewRequest, ResultResponse, ResultListResponse
from ..core.exceptions import ResourceNotFoundException, WorkflowConflictException, DataIntegrityException

class OrderService:
    def __init__(self, conn):
        self.conn = conn
        self.order_repo = OrderRepository(conn)
        self.result_repo = ResultRepository(conn)
        self.encounter_repo = EncounterRepository(conn)
        self.patient_repo = PatientRepository(conn)
        self.audit_repo = AuditRepository(conn)

    def create_order(self, payload: OrderCreate, actor: str = "ORDERING_PHYSICIAN") -> OrderResponse:
        enc = self.encounter_repo.get_by_id(payload.encounter_id)
        if not enc:
            raise ResourceNotFoundException("Encounter", payload.encounter_id)
        if enc["status"] in ("COMPLETED", "CANCELLED"):
            raise WorkflowConflictException(
                message=f"Cannot place orders for encounter in '{enc['status']}' status.",
                details={"encounter_id": payload.encounter_id, "encounter_status": enc["status"]}
            )

        data = payload.model_dump()
        order_id = self.order_repo.create(data)

        self.audit_repo.log_audit(
            entity_type="ORDER",
            entity_id=order_id,
            action="CREATE_ORDER",
            actor=actor,
            previous_state=None,
            new_state=data,
            reason=f"Clinical order placed: {payload.order_name}"
        )
        self.audit_repo.log_status_history(
            entity_type="ORDER",
            entity_id=order_id,
            from_status=None,
            to_status="ORDERED",
            actor=actor,
            reason="Order requisition submitted"
        )
        self.conn.commit()

        created = self.order_repo.get_by_id(order_id)
        return OrderResponse(**created)

    def complete_order_with_result(self, order_id: int, payload: OrderCompleteRequest) -> ResultResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Order", order_id)

        if order["order_status"] == "COMPLETED":
            raise WorkflowConflictException(
                message="Order is already completed.",
                details={"order_id": order_id}
            )
        if order["order_status"] == "CANCELLED":
            raise WorkflowConflictException(
                message="Cannot attach results to a CANCELLED order.",
                details={"order_id": order_id}
            )

        existing_res = self.result_repo.get_by_order_id(order_id)
        if existing_res:
            raise DataIntegrityException(
                message=f"Result already exists for Order ID {order_id}.",
                details={"order_id": order_id, "existing_result_id": existing_res["result_id"]}
            )

        now_str = datetime.now().isoformat()

        # 1. Insert Result
        result_data = {
            "order_id": order_id,
            "result_value": payload.result_value,
            "reference_range": payload.reference_range,
            "unit": payload.unit,
            "abnormal_flag": payload.abnormal_flag
        }
        result_id = self.result_repo.create(result_data)

        # 2. Update Order
        self.order_repo.complete_order(order_id=order_id, completed_at=now_str)

        # 3. Audit trail
        self.audit_repo.log_status_history(
            entity_type="ORDER",
            entity_id=order_id,
            from_status=order["order_status"],
            to_status="COMPLETED",
            actor=payload.actor,
            reason="Diagnostic results posted"
        )
        self.audit_repo.log_audit(
            entity_type="ORDER",
            entity_id=order_id,
            action="COMPLETE_WITH_RESULT",
            actor=payload.actor,
            previous_state={"order_status": order["order_status"]},
            new_state={"order_status": "COMPLETED", "result_id": result_id, "completed_at": now_str},
            reason="Diagnostic test completion"
        )
        self.audit_repo.log_audit(
            entity_type="RESULT",
            entity_id=result_id,
            action="POST_RESULT",
            actor=payload.actor,
            previous_state=None,
            new_state=result_data,
            reason="Initial result entry awaiting review"
        )

        self.conn.commit()

        created_res = self.result_repo.get_by_id(result_id)
        return ResultResponse(**created_res)

    def review_result(self, result_id: int, payload: ResultReviewRequest) -> ResultResponse:
        res = self.result_repo.get_by_id(result_id)
        if not res:
            raise ResourceNotFoundException("Result", result_id)

        if res["result_status"] == "REVIEWED":
            raise WorkflowConflictException(
                message="Result has already been reviewed and signed off.",
                details={"result_id": result_id, "reviewed_by": res.get("reviewed_by")}
            )

        now_str = datetime.now().isoformat()
        self.result_repo.review_result(result_id=result_id, reviewer=payload.reviewer, reviewed_at=now_str)

        self.audit_repo.log_audit(
            entity_type="RESULT",
            entity_id=result_id,
            action="CLINICAL_REVIEW_SIGNOFF",
            actor=payload.reviewer,
            previous_state={"result_status": res["result_status"]},
            new_state={"result_status": "REVIEWED", "reviewed_by": payload.reviewer, "reviewed_at": now_str},
            reason="Physician review completed"
        )
        self.conn.commit()

        updated = self.result_repo.get_by_id(result_id)
        return ResultResponse(**updated)

    def get_order(self, order_id: int) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Order", order_id)
        return OrderResponse(**order)

    def list_orders(self, encounter_id: Optional[int] = None, patient_id: Optional[int] = None,
                    status: Optional[str] = None, priority: Optional[str] = None,
                    page: int = 1, page_size: int = 50) -> OrderListResponse:
        offset = (page - 1) * page_size
        items_raw = self.order_repo.list_orders(encounter_id=encounter_id, patient_id=patient_id,
                                                status=status, priority=priority,
                                                limit=page_size, offset=offset)
        total = self.order_repo.count_orders(encounter_id=encounter_id, patient_id=patient_id,
                                            status=status, priority=priority)
        items = [OrderResponse(**r) for r in items_raw]
        return OrderListResponse(items=items, total=total, page=page, page_size=page_size)

    def list_results(self, result_status: Optional[str] = None, abnormal_only: bool = False,
                     page: int = 1, page_size: int = 50) -> ResultListResponse:
        offset = (page - 1) * page_size
        items_raw = self.result_repo.list_results(result_status=result_status, abnormal_only=abnormal_only,
                                                  limit=page_size, offset=offset)
        total = self.result_repo.count_results(result_status=result_status, abnormal_only=abnormal_only)
        items = [ResultResponse(**r) for r in items_raw]
        return ResultListResponse(items=items, total=total, page=page, page_size=page_size)
