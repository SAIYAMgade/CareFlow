from typing import Dict, Any, List
from .base import row_to_dict, rows_to_dicts

class DashboardRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_kpis(self) -> Dict[str, int]:
        cursor = self.conn.cursor()
        is_sqlite = self.conn.dialect == "sqlite"

        # 1. Appointments scheduled today
        if is_sqlite:
            cursor.execute("SELECT COUNT(*) FROM APPOINTMENTS WHERE DATE(appointment_time) = DATE('now')")
        else:
            cursor.execute("SELECT COUNT(*) FROM APPOINTMENTS WHERE TRUNC(CAST(appointment_time AS DATE)) = TRUNC(SYSDATE)")
        appts_today = cursor.fetchone()[0]

        # 2. Patients checked in
        cursor.execute("SELECT COUNT(*) FROM APPOINTMENTS WHERE status = 'CHECKED_IN'")
        checked_in = cursor.fetchone()[0]

        # 3. Patients waiting (Checked in but encounter not yet in progress or completed)
        cursor.execute("""
        SELECT COUNT(DISTINCT a.appointment_id) 
        FROM APPOINTMENTS a
        LEFT JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
        WHERE a.status = 'CHECKED_IN' AND (e.status IS NULL OR e.status = 'OPEN')
        """)
        waiting = cursor.fetchone()[0]

        # 4. Encounters in progress
        cursor.execute("SELECT COUNT(*) FROM ENCOUNTERS WHERE status IN ('OPEN', 'IN_PROGRESS', 'AWAITING_RESULTS')")
        enc_in_progress = cursor.fetchone()[0]

        # 5. Encounters completed today
        if is_sqlite:
            cursor.execute("SELECT COUNT(*) FROM ENCOUNTERS WHERE status = 'COMPLETED' AND DATE(end_time) = DATE('now')")
        else:
            cursor.execute("SELECT COUNT(*) FROM ENCOUNTERS WHERE status = 'COMPLETED' AND TRUNC(CAST(end_time AS DATE)) = TRUNC(SYSDATE)")
        row = cursor.fetchone()
        enc_completed_today = row[0] if row else 0

        # 6. Orders awaiting results
        cursor.execute("SELECT COUNT(*) FROM ORDERS WHERE order_status IN ('ORDERED', 'IN_PROGRESS')")
        orders_awaiting = cursor.fetchone()[0]

        # 7. Results awaiting review
        cursor.execute("SELECT COUNT(*) FROM RESULTS WHERE result_status = 'PENDING_REVIEW'")
        results_review = cursor.fetchone()[0]

        # 8. Open data quality issues
        cursor.execute("SELECT COUNT(*) FROM DATA_QUALITY_ISSUES WHERE resolution_status IN ('OPEN', 'INVESTIGATING')")
        dq_issues = cursor.fetchone()[0]

        return {
            "appointments_today": appts_today,
            "patients_checked_in": checked_in,
            "patients_waiting": waiting,
            "encounters_in_progress": enc_in_progress,
            "encounters_completed_today": enc_completed_today,
            "orders_awaiting_results": orders_awaiting,
            "results_awaiting_review": results_review,
            "open_data_quality_issues": dq_issues
        }

    def get_charts(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        is_sqlite = self.conn.dialect == "sqlite"

        # 1. Hourly appointment volume
        hourly_volume = []
        if is_sqlite:
            cursor.execute("""
            SELECT CAST(strftime('%H', appointment_time) AS INTEGER) as hr,
                   COUNT(*) as scheduled,
                   COUNT(CASE WHEN status IN ('CHECKED_IN', 'IN_PROGRESS', 'COMPLETED') THEN 1 END) as checked_in
            FROM APPOINTMENTS
            GROUP BY hr
            ORDER BY hr
            """)
        else:
            cursor.execute("""
            SELECT EXTRACT(HOUR FROM appointment_time) as hr,
                   COUNT(*) as scheduled,
                   COUNT(CASE WHEN status IN ('CHECKED_IN', 'IN_PROGRESS', 'COMPLETED') THEN 1 END) as checked_in
            FROM APPOINTMENTS
            GROUP BY EXTRACT(HOUR FROM appointment_time)
            ORDER BY hr
            """)
        for r in cursor.fetchall():
            hourly_volume.append({
                "hour": int(r[0]) if r[0] is not None else 8,
                "scheduled": int(r[1]),
                "checked_in": int(r[2])
            })

        # 2. Encounter status distribution
        cursor.execute("""
        SELECT status, COUNT(*) as cnt
        FROM ENCOUNTERS
        GROUP BY status
        ORDER BY cnt DESC
        """)
        encounter_dist = [{"status": r[0], "count": int(r[1])} for r in cursor.fetchall()]

        # 3. Average wait time by department
        wait_times = []
        if is_sqlite:
            cursor.execute("""
            SELECT a.department,
                   ROUND(AVG((strftime('%s', e.start_time) - strftime('%s', a.check_in_time)) / 60.0), 1) as avg_wait
            FROM APPOINTMENTS a
            JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
            WHERE a.check_in_time IS NOT NULL AND e.start_time >= a.check_in_time
            GROUP BY a.department
            ORDER BY avg_wait DESC
            """)
        else:
            cursor.execute("""
            SELECT a.department,
                   ROUND(AVG(
                       EXTRACT(DAY FROM (e.start_time - a.check_in_time)) * 1440 +
                       EXTRACT(HOUR FROM (e.start_time - a.check_in_time)) * 60 +
                       EXTRACT(MINUTE FROM (e.start_time - a.check_in_time))
                   ), 1) as avg_wait
            FROM APPOINTMENTS a
            JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
            WHERE a.check_in_time IS NOT NULL AND e.start_time >= a.check_in_time
            GROUP BY a.department
            ORDER BY avg_wait DESC
            """)
        for r in cursor.fetchall():
            wait_times.append({
                "department": r[0],
                "avg_wait_minutes": float(r[1]) if r[1] is not None else 0.0
            })

        # 4. Order turnaround time
        order_tat = []
        if is_sqlite:
            cursor.execute("""
            SELECT order_code, order_name,
                   ROUND(AVG((strftime('%s', completed_at) - strftime('%s', ordered_at)) / 3600.0), 2) as avg_tat
            FROM ORDERS
            WHERE order_status = 'COMPLETED' AND completed_at IS NOT NULL
            GROUP BY order_code, order_name
            ORDER BY avg_tat DESC
            LIMIT 6
            """)
        else:
            cursor.execute("""
            SELECT order_code, order_name,
                   ROUND(AVG(
                       EXTRACT(DAY FROM (completed_at - ordered_at)) * 24 +
                       EXTRACT(HOUR FROM (completed_at - ordered_at)) +
                       EXTRACT(MINUTE FROM (completed_at - ordered_at)) / 60
                   ), 2) as avg_tat
            FROM ORDERS
            WHERE order_status = 'COMPLETED' AND completed_at IS NOT NULL
            GROUP BY order_code, order_name
            ORDER BY avg_tat DESC
            FETCH NEXT 6 ROWS ONLY
            """)
        for r in cursor.fetchall():
            order_tat.append({
                "order_code": r[0],
                "order_name": r[1],
                "avg_turnaround_hours": float(r[2]) if r[2] is not None else 0.0
            })

        # 5. Exceptions by severity
        cursor.execute("""
        SELECT severity, COUNT(*) as cnt
        FROM DATA_QUALITY_ISSUES
        WHERE resolution_status IN ('OPEN', 'INVESTIGATING')
        GROUP BY severity
        ORDER BY 
            CASE severity 
                WHEN 'CRITICAL' THEN 1 
                WHEN 'HIGH' THEN 2 
                WHEN 'MEDIUM' THEN 3 
                ELSE 4 
            END ASC
        """)
        exceptions_sev = [{"severity": r[0], "count": int(r[1])} for r in cursor.fetchall()]

        return {
            "hourly_volume": hourly_volume,
            "encounter_distribution": encounter_dist,
            "wait_time_by_dept": wait_times,
            "order_turnaround": order_tat,
            "exceptions_by_severity": exceptions_sev
        }
