from datetime import datetime
from typing import Optional, Dict, Any
from ..repositories.appointment_repo import AppointmentRepository
from ..repositories.encounter_repo import EncounterRepository
from ..repositories.patient_repo import PatientRepository
from ..repositories.audit_repo import AuditRepository
from ..schemas.appointment import (
    AppointmentCreate, AppointmentResponse, AppointmentListResponse,
    AppointmentCheckInResponse, AppointmentReschedule, AppointmentCancel
)
from ..core.exceptions import ResourceNotFoundException, WorkflowConflictException

class AppointmentService:
    def __init__(self, conn):
        self.conn = conn
        self.repo = AppointmentRepository(conn)
        self.patient_repo = PatientRepository(conn)
        self.encounter_repo = EncounterRepository(conn)
        self.audit_repo = AuditRepository(conn)

    def create_appointment(self, payload: AppointmentCreate, actor: str = "SCHEDULER") -> AppointmentResponse:
        patient = self.patient_repo.get_by_id(payload.patient_id)
        if not patient:
            raise ResourceNotFoundException("Patient", payload.patient_id)

        data = {
            "patient_id": payload.patient_id,
            "appointment_time": payload.appointment_time,
            "appointment_type": payload.appointment_type,
            "department": payload.department,
            "provider_name": payload.provider_name
        }
        appointment_id = self.repo.create(data)
        
        self.audit_repo.log_audit(
            entity_type="APPOINTMENT",
            entity_id=appointment_id,
            action="CREATE_APPOINTMENT",
            actor=actor,
            previous_state=None,
            new_state=data,
            reason="New appointment booked"
        )
        self.audit_repo.log_status_history(
            entity_type="APPOINTMENT",
            entity_id=appointment_id,
            from_status=None,
            to_status="SCHEDULED",
            actor=actor,
            reason="Initial booking"
        )
        self.conn.commit()

        created = self.repo.get_by_id(appointment_id)
        return AppointmentResponse(**created)

    def check_in_patient(self, appointment_id: int, actor: str = "FRONT_DESK") -> AppointmentCheckInResponse:
        appt = self.repo.get_by_id(appointment_id)
        if not appt:
            raise ResourceNotFoundException("Appointment", appointment_id)

        current_status = appt["status"]
        if current_status != "SCHEDULED":
            raise WorkflowConflictException(
                message=f"Cannot check in appointment. Current status is '{current_status}'. Only SCHEDULED appointments may be checked in.",
                details={"appointment_id": appointment_id, "current_status": current_status}
            )

        now_str = datetime.now().isoformat()

        # Update appointment status
        self.repo.update_status(appointment_id=appointment_id, new_status="CHECKED_IN", check_in_time=now_str)
        self.audit_repo.log_status_history(
            entity_type="APPOINTMENT",
            entity_id=appointment_id,
            from_status=current_status,
            to_status="CHECKED_IN",
            actor=actor,
            reason="Patient arrival at clinic reception"
        )
        self.audit_repo.log_audit(
            entity_type="APPOINTMENT",
            entity_id=appointment_id,
            action="CHECK_IN",
            actor=actor,
            previous_state={"status": current_status},
            new_state={"status": "CHECKED_IN", "check_in_time": now_str},
            reason="Reception check-in"
        )

        # Atomically open corresponding Encounter
        encounter_data = {
            "patient_id": appt["patient_id"],
            "appointment_id": appointment_id,
            "encounter_type": appt["appointment_type"],
            "department": appt["department"],
            "provider_name": appt["provider_name"],
            "chief_complaint": f"Scheduled visit: {appt['appointment_type']}",
            "clinical_notes": "Patient arrived and checked in. Encounter opened for clinical triage."
        }
        encounter_id = self.encounter_repo.create(encounter_data)
        
        self.audit_repo.log_status_history(
            entity_type="ENCOUNTER",
            entity_id=encounter_id,
            from_status=None,
            to_status="OPEN",
            actor=actor,
            reason="Encounter opened automatically on check-in"
        )
        self.audit_repo.log_audit(
            entity_type="ENCOUNTER",
            entity_id=encounter_id,
            action="AUTO_OPEN_ENCOUNTER",
            actor=actor,
            previous_state=None,
            new_state={"encounter_id": encounter_id, "appointment_id": appointment_id, "status": "OPEN"},
            reason="Created on appointment check-in"
        )

        self.conn.commit()

        return AppointmentCheckInResponse(
            appointment_id=appointment_id,
            status="CHECKED_IN",
            check_in_time=now_str,
            encounter_id=encounter_id,
            message="Patient successfully checked in and clinical encounter initiated."
        )

    def cancel_appointment(self, appointment_id: int, payload: AppointmentCancel) -> AppointmentResponse:
        appt = self.repo.get_by_id(appointment_id)
        if not appt:
            raise ResourceNotFoundException("Appointment", appointment_id)

        current_status = appt["status"]
        if current_status in ("COMPLETED", "CANCELLED", "NO_SHOW"):
            raise WorkflowConflictException(
                message=f"Cannot cancel appointment with status '{current_status}'.",
                details={"appointment_id": appointment_id, "current_status": current_status}
            )

        self.repo.update_status(appointment_id=appointment_id, new_status="CANCELLED", cancel_reason=payload.cancel_reason)
        self.audit_repo.log_status_history(
            entity_type="APPOINTMENT",
            entity_id=appointment_id,
            from_status=current_status,
            to_status="CANCELLED",
            actor=payload.actor,
            reason=payload.cancel_reason
        )
        self.audit_repo.log_audit(
            entity_type="APPOINTMENT",
            entity_id=appointment_id,
            action="CANCEL_APPOINTMENT",
            actor=payload.actor,
            previous_state={"status": current_status},
            new_state={"status": "CANCELLED", "cancel_reason": payload.cancel_reason},
            reason=payload.cancel_reason
        )
        self.conn.commit()

        updated = self.repo.get_by_id(appointment_id)
        return AppointmentResponse(**updated)

    def reschedule_appointment(self, appointment_id: int, payload: AppointmentReschedule) -> AppointmentResponse:
        appt = self.repo.get_by_id(appointment_id)
        if not appt:
            raise ResourceNotFoundException("Appointment", appointment_id)

        current_status = appt["status"]
        if current_status != "SCHEDULED":
            raise WorkflowConflictException(
                message=f"Only SCHEDULED appointments can be rescheduled. Current status is '{current_status}'.",
                details={"appointment_id": appointment_id, "current_status": current_status}
            )

        old_time = appt["appointment_time"]
        self.repo.reschedule(appointment_id=appointment_id, new_time=payload.new_appointment_time)
        self.audit_repo.log_audit(
            entity_type="APPOINTMENT",
            entity_id=appointment_id,
            action="RESCHEDULE_APPOINTMENT",
            actor=payload.actor,
            previous_state={"appointment_time": old_time},
            new_state={"appointment_time": payload.new_appointment_time},
            reason=payload.reason
        )
        self.conn.commit()

        updated = self.repo.get_by_id(appointment_id)
        return AppointmentResponse(**updated)

    def get_appointment(self, appointment_id: int) -> AppointmentResponse:
        appt = self.repo.get_by_id(appointment_id)
        if not appt:
            raise ResourceNotFoundException("Appointment", appointment_id)
        return AppointmentResponse(**appt)

    def list_appointments(self, date_str: Optional[str] = None, department: Optional[str] = None,
                           status: Optional[str] = None, patient_id: Optional[int] = None,
                           page: int = 1, page_size: int = 50) -> AppointmentListResponse:
        offset = (page - 1) * page_size
        items_raw = self.repo.list_appointments(date_str=date_str, department=department,
                                               status=status, patient_id=patient_id,
                                               limit=page_size, offset=offset)
        total = self.repo.count_appointments(date_str=date_str, department=department,
                                            status=status, patient_id=patient_id)
        items = [AppointmentResponse(**r) for r in items_raw]
        return AppointmentListResponse(items=items, total=total, page=page, page_size=page_size)
