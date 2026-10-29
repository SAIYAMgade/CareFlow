from datetime import datetime
from typing import Optional, Dict, Any
from ..repositories.encounter_repo import EncounterRepository
from ..repositories.appointment_repo import AppointmentRepository
from ..repositories.patient_repo import PatientRepository
from ..repositories.order_repo import OrderRepository
from ..repositories.audit_repo import AuditRepository
from ..schemas.encounter import (
    EncounterCreate, EncounterResponse, EncounterListResponse,
    EncounterStatusUpdate, EncounterNotesUpdate
)
from ..core.exceptions import ResourceNotFoundException, WorkflowConflictException

class EncounterService:
    def __init__(self, conn):
        self.conn = conn
        self.repo = EncounterRepository(conn)
        self.appt_repo = AppointmentRepository(conn)
        self.patient_repo = PatientRepository(conn)
        self.order_repo = OrderRepository(conn)
        self.audit_repo = AuditRepository(conn)

    def create_encounter(self, payload: EncounterCreate, actor: str = "CLINICIAN") -> EncounterResponse:
        patient = self.patient_repo.get_by_id(payload.patient_id)
        if not patient:
            raise ResourceNotFoundException("Patient", payload.patient_id)

        data = payload.model_dump()
        encounter_id = self.repo.create(data)

        self.audit_repo.log_audit(
            entity_type="ENCOUNTER",
            entity_id=encounter_id,
            action="CREATE_ENCOUNTER",
            actor=actor,
            previous_state=None,
            new_state=data,
            reason="Ad-hoc or outpatient encounter created"
        )
        self.audit_repo.log_status_history(
            entity_type="ENCOUNTER",
            entity_id=encounter_id,
            from_status=None,
            to_status="OPEN",
            actor=actor,
            reason="Encounter opened"
        )
        self.conn.commit()

        created = self.repo.get_by_id(encounter_id)
        return EncounterResponse(**created)

    def update_status(self, encounter_id: int, payload: EncounterStatusUpdate) -> EncounterResponse:
        enc = self.repo.get_by_id(encounter_id)
        if not enc:
            raise ResourceNotFoundException("Encounter", encounter_id)

        current_status = enc["status"]
        target_status = payload.new_status

        if current_status == "COMPLETED":
            raise WorkflowConflictException(
                message="Encounter is already COMPLETED and closed to modification.",
                details={"encounter_id": encounter_id, "current_status": current_status}
            )
        if current_status == "CANCELLED":
            raise WorkflowConflictException(
                message="Cannot update status of a CANCELLED encounter.",
                details={"encounter_id": encounter_id, "current_status": current_status}
            )

        # WORKFLOW INTEGRITY RULE: Check for pending orders before completion
        if target_status == "COMPLETED":
            pending_orders = self.order_repo.count_pending_by_encounter(encounter_id)
            if pending_orders > 0:
                raise WorkflowConflictException(
                    message=f"Encounter cannot be completed: {pending_orders} laboratory/clinical order(s) remain pending results.",
                    details={"encounter_id": encounter_id, "pending_orders_count": pending_orders}
                )

        now_str = datetime.now().isoformat()
        end_time = now_str if target_status == "COMPLETED" else None

        self.repo.update_status(encounter_id=encounter_id, new_status=target_status,
                                end_time=end_time, notes=payload.clinical_notes)

        self.audit_repo.log_status_history(
            entity_type="ENCOUNTER",
            entity_id=encounter_id,
            from_status=current_status,
            to_status=target_status,
            actor=payload.actor,
            reason=payload.reason or f"Transitioned to {target_status}"
        )
        self.audit_repo.log_audit(
            entity_type="ENCOUNTER",
            entity_id=encounter_id,
            action=f"TRANSITION_TO_{target_status}",
            actor=payload.actor,
            previous_state={"status": current_status},
            new_state={"status": target_status, "end_time": end_time},
            reason=payload.reason or "Clinical workflow transition"
        )

        # If completed and linked to an appointment, complete the appointment as well
        if target_status == "COMPLETED" and enc.get("appointment_id"):
            appt_id = enc["appointment_id"]
            self.appt_repo.update_status(appointment_id=appt_id, new_status="COMPLETED")
            self.audit_repo.log_status_history(
                entity_type="APPOINTMENT",
                entity_id=appt_id,
                from_status="CHECKED_IN",
                to_status="COMPLETED",
                actor=payload.actor,
                reason="Linked encounter completed"
            )

        self.conn.commit()

        updated = self.repo.get_by_id(encounter_id)
        return EncounterResponse(**updated)

    def update_notes(self, encounter_id: int, payload: EncounterNotesUpdate) -> EncounterResponse:
        enc = self.repo.get_by_id(encounter_id)
        if not enc:
            raise ResourceNotFoundException("Encounter", encounter_id)

        self.repo.update_notes(encounter_id, payload.clinical_notes)
        self.audit_repo.log_audit(
            entity_type="ENCOUNTER",
            entity_id=encounter_id,
            action="UPDATE_CLINICAL_NOTES",
            actor=payload.actor,
            previous_state={"clinical_notes": enc.get("clinical_notes")},
            new_state={"clinical_notes": payload.clinical_notes},
            reason="Clinical documentation update"
        )
        self.conn.commit()

        updated = self.repo.get_by_id(encounter_id)
        return EncounterResponse(**updated)

    def get_encounter(self, encounter_id: int) -> EncounterResponse:
        enc = self.repo.get_by_id(encounter_id)
        if not enc:
            raise ResourceNotFoundException("Encounter", encounter_id)
        return EncounterResponse(**enc)

    def list_encounters(self, patient_id: Optional[int] = None, department: Optional[str] = None,
                        status: Optional[str] = None, page: int = 1, page_size: int = 50) -> EncounterListResponse:
        offset = (page - 1) * page_size
        items_raw = self.repo.list_encounters(patient_id=patient_id, department=department,
                                             status=status, limit=page_size, offset=offset)
        total = self.repo.count_encounters(patient_id=patient_id, department=department, status=status)
        items = [EncounterResponse(**r) for r in items_raw]
        return EncounterListResponse(items=items, total=total, page=page, page_size=page_size)
