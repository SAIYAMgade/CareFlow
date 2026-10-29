import time
import io
import csv
from typing import Dict, Any, List, Optional
from ..core.exceptions import ResourceNotFoundException, ValidationException
from ..repositories.base import rows_to_dicts
from ..schemas.report import ReportCatalogItem, ReportParameter, ReportExecutionResult

REPORT_CATALOG = [
    ReportCatalogItem(
        id="RPT_01_DAILY_SCHEDULE",
        title="Daily Appointment Operational Schedule",
        category="Operational",
        description="Comprehensive daily clinic schedule showing appointment status, patient details, arrival timestamps, and waiting durations.",
        business_question="What is the complete schedule and arrival status of all patients for a given date and clinic department?",
        parameters=[
            ReportParameter(name="p_target_date", label="Target Date (YYYY-MM-DD)", type="date", default=None),
            ReportParameter(name="p_department", label="Department", type="select", default=None,
                            options=["All", "Cardiology", "Endocrinology", "Family Medicine", "Pediatrics", "Urgent Care"]),
            ReportParameter(name="p_status", label="Appointment Status", type="select", default=None,
                            options=["All", "SCHEDULED", "CHECKED_IN", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW"])
        ]
    ),
    ReportCatalogItem(
        id="RPT_02_WAITING_TIME",
        title="Patient Waiting Time Analysis",
        category="Clinical Operations",
        description="Detailed analysis of clinic waiting times (minutes between check-in and encounter start) aggregated by department and arrival hour.",
        business_question="How long are checked-in patients waiting before clinician triage across each department and hour of the day?",
        parameters=[
            ReportParameter(name="p_department", label="Department", type="select", default=None,
                            options=["All", "Cardiology", "Endocrinology", "Family Medicine", "Pediatrics", "Urgent Care"])
        ]
    ),
    ReportCatalogItem(
        id="RPT_03_ENCOUNTER_COMPLETION",
        title="Encounter Completion & Cycle Time",
        category="Clinical Operations",
        description="Encounter duration analysis (minutes from visit start to signoff) broken down by provider, department, and encounter type.",
        business_question="What is the clinical visit cycle time and provider throughput across appointment types and departments?",
        parameters=[
            ReportParameter(name="p_department", label="Department", type="select", default=None,
                            options=["All", "Cardiology", "Endocrinology", "Family Medicine", "Pediatrics", "Urgent Care"])
        ]
    ),
    ReportCatalogItem(
        id="RPT_04_PENDING_ORDERS",
        title="Pending Clinical Orders Backlog",
        category="Diagnostic",
        description="Current backlog of active diagnostic orders awaiting laboratory results, sorted by priority and order aging.",
        business_question="Which clinical orders are pending laboratory results and how long have urgent or stat tests been open?",
        parameters=[
            ReportParameter(name="p_priority", label="Order Priority", type="select", default=None,
                            options=["All", "STAT", "URGENT", "ROUTINE"]),
            ReportParameter(name="p_department", label="Department", type="select", default=None,
                            options=["All", "Cardiology", "Endocrinology", "Family Medicine", "Pediatrics", "Urgent Care"])
        ]
    ),
    ReportCatalogItem(
        id="RPT_05_AWAITING_REVIEW",
        title="Completed Orders Awaiting Review",
        category="Diagnostic",
        description="Completed laboratory results awaiting physician clinical review, with critical and abnormal results prioritized first.",
        business_question="Which diagnostic results have been completed but not yet signed off, and are there critical abnormalities pending review?",
        parameters=[
            ReportParameter(name="p_abnormal_only", label="Abnormal Results Only", type="select", default="All",
                            options=["All", "Y", "N"])
        ]
    ),
    ReportCatalogItem(
        id="RPT_06_ORDER_TURNAROUND",
        title="Order Turnaround Time (TAT) Analysis",
        category="Diagnostic",
        description="Turnaround time (hours between requisition and completion) by laboratory test code and priority level.",
        business_question="What is the average and maximum diagnostic turnaround time for each lab test type?",
        parameters=[]
    ),
    ReportCatalogItem(
        id="RPT_07_CANCELLATIONS_NOSHOW",
        title="Cancellation & No-Show Pattern Analysis",
        category="Operational",
        description="Departmental breakdown of scheduled vs. cancelled vs. no-show appointments, calculating total lost clinical capacity.",
        business_question="What is our lost clinical capacity rate and which departments experience high no-show volumes?",
        parameters=[
            ReportParameter(name="p_department", label="Department", type="select", default=None,
                            options=["All", "Cardiology", "Endocrinology", "Family Medicine", "Pediatrics", "Urgent Care"])
        ]
    ),
    ReportCatalogItem(
        id="RPT_08_DATA_QUALITY",
        title="Data Quality Exception Audit",
        category="Governance",
        description="Live audit of open data-integrity violations, rule codes, severity distribution, and aging since detection.",
        business_question="What data discrepancies or broken workflow invariants currently threaten operational and clinical reporting?",
        parameters=[
            ReportParameter(name="p_severity", label="Severity Filter", type="select", default=None,
                            options=["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
        ]
    )
]

class ReportService:
    def __init__(self, conn):
        self.conn = conn

    def get_catalog(self) -> List[ReportCatalogItem]:
        return REPORT_CATALOG

    def _get_report_meta(self, report_id: str) -> ReportCatalogItem:
        for item in REPORT_CATALOG:
            if item.id == report_id:
                return item
        raise ResourceNotFoundException("Report", report_id)

    def execute_report(self, report_id: str, params: Dict[str, Any], page: int = 1, page_size: int = 50) -> ReportExecutionResult:
        meta = self._get_report_meta(report_id)
        is_sqlite = self.conn.dialect == "sqlite"
        cursor = self.conn.cursor()

        # Sanitize parameters (convert "All" to None)
        sanitized_params: Dict[str, Any] = {}
        for k, v in params.items():
            if v in ("All", "", None):
                sanitized_params[k] = None
            else:
                sanitized_params[k] = v

        sql = ""
        query_params: Dict[str, Any] = {}

        if report_id == "RPT_01_DAILY_SCHEDULE":
            query_params = {
                "dept": sanitized_params.get("p_department"),
                "status": sanitized_params.get("p_status"),
                "target_date": sanitized_params.get("p_target_date")
            }
            if is_sqlite:
                sql = """
                SELECT 
                    a.appointment_id,
                    a.appointment_time,
                    a.department,
                    a.provider_name,
                    a.appointment_type,
                    a.status AS appointment_status,
                    p.patient_id,
                    p.mrn,
                    p.first_name || ' ' || p.last_name AS patient_name,
                    a.check_in_time,
                    e.encounter_id,
                    e.status AS encounter_status
                FROM APPOINTMENTS a
                JOIN PATIENTS p ON a.patient_id = p.patient_id
                LEFT JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
                WHERE (:dept IS NULL OR a.department = :dept)
                  AND (:status IS NULL OR a.status = :status)
                  AND (:target_date IS NULL OR DATE(a.appointment_time) = :target_date)
                ORDER BY a.appointment_time ASC
                """
            else:
                sql = """
                SELECT 
                    a.appointment_id,
                    TO_CHAR(a.appointment_time, 'YYYY-MM-DD HH24:MI:SS') as appointment_time,
                    a.department,
                    a.provider_name,
                    a.appointment_type,
                    a.status AS appointment_status,
                    p.patient_id,
                    p.mrn,
                    p.first_name || ' ' || p.last_name AS patient_name,
                    TO_CHAR(a.check_in_time, 'YYYY-MM-DD HH24:MI:SS') as check_in_time,
                    e.encounter_id,
                    e.status AS encounter_status
                FROM APPOINTMENTS a
                JOIN PATIENTS p ON a.patient_id = p.patient_id
                LEFT JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
                WHERE (:dept IS NULL OR a.department = :dept)
                  AND (:status IS NULL OR a.status = :status)
                  AND (:target_date IS NULL OR TRUNC(CAST(a.appointment_time AS DATE)) = TO_DATE(:target_date, 'YYYY-MM-DD'))
                ORDER BY a.appointment_time ASC
                """

        elif report_id == "RPT_02_WAITING_TIME":
            query_params = {"dept": sanitized_params.get("p_department")}
            if is_sqlite:
                sql = """
                SELECT 
                    a.department,
                    CAST(strftime('%H', a.check_in_time) AS INTEGER) AS arrival_hour,
                    COUNT(*) AS total_patients_seen,
                    ROUND(AVG((strftime('%s', e.start_time) - strftime('%s', a.check_in_time)) / 60.0), 1) AS avg_wait_minutes,
                    ROUND(MIN((strftime('%s', e.start_time) - strftime('%s', a.check_in_time)) / 60.0), 1) AS min_wait_minutes,
                    ROUND(MAX((strftime('%s', e.start_time) - strftime('%s', a.check_in_time)) / 60.0), 1) AS max_wait_minutes
                FROM APPOINTMENTS a
                JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
                WHERE a.check_in_time IS NOT NULL AND e.start_time >= a.check_in_time
                  AND (:dept IS NULL OR a.department = :dept)
                GROUP BY a.department, arrival_hour
                ORDER BY a.department, arrival_hour
                """
            else:
                sql = """
                SELECT 
                    a.department,
                    EXTRACT(HOUR FROM a.check_in_time) AS arrival_hour,
                    COUNT(*) AS total_patients_seen,
                    ROUND(AVG(
                        EXTRACT(DAY FROM (e.start_time - a.check_in_time)) * 1440 +
                        EXTRACT(HOUR FROM (e.start_time - a.check_in_time)) * 60 +
                        EXTRACT(MINUTE FROM (e.start_time - a.check_in_time))
                    ), 1) AS avg_wait_minutes,
                    ROUND(MIN(
                        EXTRACT(DAY FROM (e.start_time - a.check_in_time)) * 1440 +
                        EXTRACT(HOUR FROM (e.start_time - a.check_in_time)) * 60 +
                        EXTRACT(MINUTE FROM (e.start_time - a.check_in_time))
                    ), 1) AS min_wait_minutes,
                    ROUND(MAX(
                        EXTRACT(DAY FROM (e.start_time - a.check_in_time)) * 1440 +
                        EXTRACT(HOUR FROM (e.start_time - a.check_in_time)) * 60 +
                        EXTRACT(MINUTE FROM (e.start_time - a.check_in_time))
                    ), 1) AS max_wait_minutes
                FROM APPOINTMENTS a
                JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
                WHERE a.check_in_time IS NOT NULL AND e.start_time >= a.check_in_time
                  AND (:dept IS NULL OR a.department = :dept)
                GROUP BY a.department, EXTRACT(HOUR FROM a.check_in_time)
                ORDER BY a.department, arrival_hour
                """

        elif report_id == "RPT_03_ENCOUNTER_COMPLETION":
            query_params = {"dept": sanitized_params.get("p_department")}
            if is_sqlite:
                sql = """
                SELECT 
                    department,
                    encounter_type,
                    provider_name,
                    COUNT(*) AS completed_encounters_count,
                    ROUND(AVG((strftime('%s', end_time) - strftime('%s', start_time)) / 60.0), 1) AS avg_duration_minutes,
                    ROUND(MIN((strftime('%s', end_time) - strftime('%s', start_time)) / 60.0), 1) AS min_duration_minutes,
                    ROUND(MAX((strftime('%s', end_time) - strftime('%s', start_time)) / 60.0), 1) AS max_duration_minutes
                FROM ENCOUNTERS
                WHERE status = 'COMPLETED' AND end_time IS NOT NULL
                  AND (:dept IS NULL OR department = :dept)
                GROUP BY department, encounter_type, provider_name
                ORDER BY department, encounter_type, provider_name
                """
            else:
                sql = """
                SELECT 
                    department,
                    encounter_type,
                    provider_name,
                    COUNT(*) AS completed_encounters_count,
                    ROUND(AVG(
                        EXTRACT(DAY FROM (end_time - start_time)) * 1440 +
                        EXTRACT(HOUR FROM (end_time - start_time)) * 60 +
                        EXTRACT(MINUTE FROM (end_time - start_time))
                    ), 1) AS avg_duration_minutes,
                    ROUND(MIN(
                        EXTRACT(DAY FROM (end_time - start_time)) * 1440 +
                        EXTRACT(HOUR FROM (end_time - start_time)) * 60 +
                        EXTRACT(MINUTE FROM (end_time - start_time))
                    ), 1) AS min_duration_minutes,
                    ROUND(MAX(
                        EXTRACT(DAY FROM (end_time - start_time)) * 1440 +
                        EXTRACT(HOUR FROM (end_time - start_time)) * 60 +
                        EXTRACT(MINUTE FROM (end_time - start_time))
                    ), 1) AS max_duration_minutes
                FROM ENCOUNTERS
                WHERE status = 'COMPLETED' AND end_time IS NOT NULL
                  AND (:dept IS NULL OR department = :dept)
                GROUP BY department, encounter_type, provider_name
                ORDER BY department, encounter_type, provider_name
                """

        elif report_id == "RPT_04_PENDING_ORDERS":
            query_params = {
                "priority": sanitized_params.get("p_priority"),
                "dept": sanitized_params.get("p_department")
            }
            if is_sqlite:
                sql = """
                SELECT 
                    o.order_id,
                    o.order_code,
                    o.order_name,
                    o.priority,
                    o.order_status,
                    o.ordered_at,
                    ROUND((strftime('%s', 'now') - strftime('%s', o.ordered_at)) / 3600.0, 1) AS age_hours,
                    p.mrn,
                    p.first_name || ' ' || p.last_name AS patient_name,
                    e.department,
                    o.ordered_by
                FROM ORDERS o
                JOIN PATIENTS p ON o.patient_id = p.patient_id
                JOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id
                WHERE o.order_status IN ('ORDERED', 'IN_PROGRESS')
                  AND (:priority IS NULL OR o.priority = :priority)
                  AND (:dept IS NULL OR e.department = :dept)
                ORDER BY 
                    CASE o.priority WHEN 'STAT' THEN 1 WHEN 'URGENT' THEN 2 ELSE 3 END,
                    o.ordered_at ASC
                """
            else:
                sql = """
                SELECT 
                    o.order_id,
                    o.order_code,
                    o.order_name,
                    o.priority,
                    o.order_status,
                    TO_CHAR(o.ordered_at, 'YYYY-MM-DD HH24:MI:SS') as ordered_at,
                    ROUND(
                        EXTRACT(DAY FROM (SYSTIMESTAMP - o.ordered_at)) * 24 +
                        EXTRACT(HOUR FROM (SYSTIMESTAMP - o.ordered_at)) +
                        EXTRACT(MINUTE FROM (SYSTIMESTAMP - o.ordered_at)) / 60,
                        1
                    ) AS age_hours,
                    p.mrn,
                    p.first_name || ' ' || p.last_name AS patient_name,
                    e.department,
                    o.ordered_by
                FROM ORDERS o
                JOIN PATIENTS p ON o.patient_id = p.patient_id
                JOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id
                WHERE o.order_status IN ('ORDERED', 'IN_PROGRESS')
                  AND (:priority IS NULL OR o.priority = :priority)
                  AND (:dept IS NULL OR e.department = :dept)
                ORDER BY 
                    CASE o.priority WHEN 'STAT' THEN 1 WHEN 'URGENT' THEN 2 ELSE 3 END,
                    o.ordered_at ASC
                """

        elif report_id == "RPT_05_AWAITING_REVIEW":
            abnormal_only = sanitized_params.get("p_abnormal_only") == "Y"
            sql = f"""
            SELECT 
                r.result_id,
                r.result_time,
                r.result_value,
                r.unit,
                r.reference_range,
                r.abnormal_flag,
                r.result_status,
                o.order_code,
                o.order_name,
                o.priority,
                p.mrn,
                p.first_name || ' ' || p.last_name AS patient_name,
                e.department
            FROM RESULTS r
            JOIN ORDERS o ON r.order_id = o.order_id
            JOIN PATIENTS p ON o.patient_id = p.patient_id
            JOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id
            WHERE r.result_status = 'PENDING_REVIEW'
              {'AND r.abnormal_flag IN ("HIGH", "LOW", "CRITICAL")' if abnormal_only else ''}
            ORDER BY 
                CASE r.abnormal_flag WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'LOW' THEN 3 ELSE 4 END,
                r.result_time ASC
            """

        elif report_id == "RPT_06_ORDER_TURNAROUND":
            if is_sqlite:
                sql = """
                SELECT 
                    order_code,
                    order_name,
                    priority,
                    COUNT(*) AS total_completed_orders,
                    ROUND(AVG((strftime('%s', completed_at) - strftime('%s', ordered_at)) / 3600.0), 2) AS avg_turnaround_hours,
                    ROUND(MIN((strftime('%s', completed_at) - strftime('%s', ordered_at)) / 3600.0), 2) AS min_turnaround_hours,
                    ROUND(MAX((strftime('%s', completed_at) - strftime('%s', ordered_at)) / 3600.0), 2) AS max_turnaround_hours
                FROM ORDERS
                WHERE order_status = 'COMPLETED' AND completed_at IS NOT NULL
                GROUP BY order_code, order_name, priority
                ORDER BY avg_turnaround_hours DESC
                """
            else:
                sql = """
                SELECT 
                    order_code,
                    order_name,
                    priority,
                    COUNT(*) AS total_completed_orders,
                    ROUND(AVG(
                        EXTRACT(DAY FROM (completed_at - ordered_at)) * 24 +
                        EXTRACT(HOUR FROM (completed_at - ordered_at)) +
                        EXTRACT(MINUTE FROM (completed_at - ordered_at)) / 60
                    ), 2) AS avg_turnaround_hours,
                    ROUND(MIN(
                        EXTRACT(DAY FROM (completed_at - ordered_at)) * 24 +
                        EXTRACT(HOUR FROM (completed_at - ordered_at)) +
                        EXTRACT(MINUTE FROM (completed_at - ordered_at)) / 60
                    ), 2) AS min_turnaround_hours,
                    ROUND(MAX(
                        EXTRACT(DAY FROM (completed_at - ordered_at)) * 24 +
                        EXTRACT(HOUR FROM (completed_at - ordered_at)) +
                        EXTRACT(MINUTE FROM (completed_at - ordered_at)) / 60
                    ), 2) AS max_turnaround_hours
                FROM ORDERS
                WHERE order_status = 'COMPLETED' AND completed_at IS NOT NULL
                GROUP BY order_code, order_name, priority
                ORDER BY avg_turnaround_hours DESC
                """

        elif report_id == "RPT_07_CANCELLATIONS_NOSHOW":
            query_params = {"dept": sanitized_params.get("p_department")}
            sql = """
            SELECT 
                department,
                appointment_type,
                COUNT(*) AS total_booked,
                COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) AS completed_count,
                COUNT(CASE WHEN status = 'CANCELLED' THEN 1 END) AS cancelled_count,
                COUNT(CASE WHEN status = 'NO_SHOW' THEN 1 END) AS noshow_count,
                ROUND((COUNT(CASE WHEN status = 'CANCELLED' THEN 1 END) * 100.0) / COUNT(*), 1) AS cancellation_rate_pct,
                ROUND((COUNT(CASE WHEN status = 'NO_SHOW' THEN 1 END) * 100.0) / COUNT(*), 1) AS noshow_rate_pct,
                ROUND(((COUNT(CASE WHEN status = 'CANCELLED' THEN 1 END) + COUNT(CASE WHEN status = 'NO_SHOW' THEN 1 END)) * 100.0) / COUNT(*), 1) AS lost_capacity_pct
            FROM APPOINTMENTS
            WHERE (:dept IS NULL OR department = :dept)
            GROUP BY department, appointment_type
            ORDER BY lost_capacity_pct DESC, department ASC
            """

        elif report_id == "RPT_08_DATA_QUALITY":
            query_params = {"severity": sanitized_params.get("p_severity")}
            sql = """
            SELECT 
                issue_id,
                rule_code,
                severity,
                affected_entity,
                entity_id,
                detection_time,
                description,
                investigation_steps,
                resolution_status,
                resolved_by
            FROM DATA_QUALITY_ISSUES
            WHERE (:severity IS NULL OR severity = :severity)
            ORDER BY 
                CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,
                issue_id DESC
            """

        start_t = time.perf_counter()
        cursor.execute(sql, query_params)
        all_rows = rows_to_dicts(cursor, cursor.fetchall())
        execution_time_ms = round((time.perf_counter() - start_t) * 1000, 2)

        total_rows = len(all_rows)
        columns = list(all_rows[0].keys()) if all_rows else []

        # Paginate results
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_rows = all_rows[start_idx:end_idx]

        return ReportExecutionResult(
            report_id=report_id,
            title=meta.title,
            columns=columns,
            rows=paged_rows,
            total_rows=total_rows,
            page=page,
            page_size=page_size,
            executed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            execution_time_ms=execution_time_ms,
            dialect=self.conn.dialect
        )

    def export_csv(self, report_id: str, params: Dict[str, Any]) -> str:
        # Run report without pagination (up to 5000 rows)
        res = self.execute_report(report_id, params, page=1, page_size=5000)
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        if res.columns:
            writer.writerow(res.columns)
            for row in res.rows:
                row_vals = []
                for col in res.columns:
                    val = str(row.get(col, ""))
                    # Formula injection safety: sanitize leading =, +, -, @, \t, \r
                    if val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
                        val = f"'{val}"
                    row_vals.append(val)
                writer.writerow(row_vals)

        return output.getvalue()
