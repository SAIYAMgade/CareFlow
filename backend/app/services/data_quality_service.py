from datetime import datetime
from typing import Optional, List, Dict, Any
from ..repositories.data_quality_repo import DataQualityRepository
from ..repositories.audit_repo import AuditRepository
from ..schemas.data_quality import (
    DataQualityIssueResponse, DataQualityResolveRequest, DataQualityScanResult
)
from ..core.exceptions import ResourceNotFoundException, WorkflowConflictException

class DataQualityService:
    def __init__(self, conn):
        self.conn = conn
        self.repo = DataQualityRepository(conn)
        self.audit_repo = AuditRepository(conn)

    def run_live_audit_scan(self, actor: str = "SYSTEM_AUDITOR") -> DataQualityScanResult:
        """
        Executes explicit, testable data quality invariant rules across the database.
        Detects broken invariants, invalid timestamp sequences, and broken state relationships.
        """
        cursor = self.conn.cursor()
        is_sqlite = self.conn.dialect == "sqlite"
        rules_scanned = 5
        new_issues = 0

        # Rule 1: Appointments checked in without check_in_time
        cursor.execute("""
        SELECT appointment_id
        FROM APPOINTMENTS
        WHERE status = 'CHECKED_IN' AND check_in_time IS NULL
        """)
        for r in cursor.fetchall():
            appt_id = r[0]
            self.repo.record_issue(
                rule_code="DQ_MISSING_CHECKIN_TIME",
                severity="HIGH",
                affected_entity="APPOINTMENT",
                entity_id=appt_id,
                description=f"Appointment {appt_id} has status 'CHECKED_IN' but arrival timestamp is NULL.",
                steps="Review reception audit log; backfill arrival timestamp or reset state to SCHEDULED."
            )
            new_issues += 1

        # Rule 2: Orders marked COMPLETED without completed_at timestamp
        cursor.execute("""
        SELECT order_id
        FROM ORDERS
        WHERE order_status = 'COMPLETED' AND completed_at IS NULL
        """)
        for r in cursor.fetchall():
            order_id = r[0]
            self.repo.record_issue(
                rule_code="DQ_MISSING_COMPLETION_TIME",
                severity="MEDIUM",
                affected_entity="ORDER",
                entity_id=order_id,
                description=f"Order {order_id} has status 'COMPLETED' but completed_at is NULL.",
                steps="Inspect laboratory interface log; backfill completion timestamp from linked Result."
            )
            new_issues += 1

        # Rule 3: Encounters marked COMPLETED despite having pending orders
        cursor.execute("""
        SELECT e.encounter_id, COUNT(o.order_id)
        FROM ENCOUNTERS e
        JOIN ORDERS o ON e.encounter_id = o.encounter_id
        WHERE e.status = 'COMPLETED'
          AND o.order_status IN ('ORDERED', 'IN_PROGRESS')
        GROUP BY e.encounter_id
        """)
        for r in cursor.fetchall():
            enc_id, pending_cnt = r[0], r[1]
            self.repo.record_issue(
                rule_code="DQ_COMPLETED_ENC_WITH_PENDING_ORDERS",
                severity="CRITICAL",
                affected_entity="ENCOUNTER",
                entity_id=enc_id,
                description=f"Encounter {enc_id} closed as COMPLETED but has {pending_cnt} order(s) awaiting lab results.",
                steps="Contact ordering clinician; confirm whether pending tests were cancelled or missed."
            )
            new_issues += 1

        # Rule 4: Encounters with end_time preceding start_time
        if is_sqlite:
            cursor.execute("""
            SELECT encounter_id
            FROM ENCOUNTERS
            WHERE end_time IS NOT NULL AND datetime(end_time) < datetime(start_time)
            """)
        else:
            cursor.execute("""
            SELECT encounter_id
            FROM ENCOUNTERS
            WHERE end_time IS NOT NULL AND end_time < start_time
            """)
        for r in cursor.fetchall():
            enc_id = r[0]
            self.repo.record_issue(
                rule_code="DQ_INVALID_TIMESTAMP_SEQUENCE",
                severity="CRITICAL",
                affected_entity="ENCOUNTER",
                entity_id=enc_id,
                description=f"Encounter {enc_id} has end_time recorded earlier than start_time.",
                steps="Verify device/server time zone settings; adjust end_time using audit trail."
            )
            new_issues += 1

        # Rule 5: Results without valid order reference
        cursor.execute("""
        SELECT r.result_id
        FROM RESULTS r
        LEFT JOIN ORDERS o ON r.order_id = o.order_id
        WHERE o.order_id IS NULL
        """)
        for r in cursor.fetchall():
            res_id = r[0]
            self.repo.record_issue(
                rule_code="DQ_ORPHANED_RESULT",
                severity="CRITICAL",
                affected_entity="RESULT",
                entity_id=res_id,
                description=f"Result {res_id} references a nonexistent or deleted Order.",
                steps="Trace HL7/FHIR message source; associate result with valid order or quarantine."
            )
            new_issues += 1

        self.conn.commit()

        open_total = self.repo.count_issues(status="OPEN")
        return DataQualityScanResult(
            scanned_rules_count=rules_scanned,
            new_issues_found=new_issues,
            open_issues_total=open_total,
            scanned_at=datetime.now().isoformat()
        )

    def resolve_issue(self, issue_id: int, payload: DataQualityResolveRequest) -> DataQualityIssueResponse:
        issue = self.repo.get_by_id(issue_id)
        if not issue:
            raise ResourceNotFoundException("DataQualityIssue", issue_id)

        if issue["resolution_status"] in ("RESOLVED", "FALSE_POSITIVE"):
            raise WorkflowConflictException(
                message=f"Data quality issue is already {issue['resolution_status']}.",
                details={"issue_id": issue_id, "current_status": issue["resolution_status"]}
            )

        now_str = datetime.now().isoformat()
        self.repo.resolve_issue(
            issue_id=issue_id,
            resolved_by=payload.resolved_by,
            status=payload.resolution_status,
            notes=payload.remediation_notes,
            resolved_at=now_str
        )

        self.audit_repo.log_audit(
            entity_type="DATA_QUALITY_ISSUE",
            entity_id=issue_id,
            action="RESOLVE_DATA_QUALITY_ISSUE",
            actor=payload.resolved_by,
            previous_state={"resolution_status": issue["resolution_status"]},
            new_state={
                "resolution_status": payload.resolution_status,
                "remediation_notes": payload.remediation_notes,
                "resolved_at": now_str
            },
            reason="Controlled data remediation workflow"
        )
        self.conn.commit()

        updated = self.repo.get_by_id(issue_id)
        return DataQualityIssueResponse(**updated)

    def list_issues(self, status: Optional[str] = None, severity: Optional[str] = None,
                    entity: Optional[str] = None, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        offset = (page - 1) * page_size
        raw_items = self.repo.list_issues(status=status, severity=severity, entity=entity,
                                          limit=page_size, offset=offset)
        total = self.repo.count_issues(status=status, severity=severity, entity=entity)
        items = [DataQualityIssueResponse(**r) for r in raw_items]
        return {"items": items, "total": total, "page": page, "page_size": page_size}
