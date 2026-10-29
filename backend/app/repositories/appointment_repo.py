from typing import Optional, List, Dict, Any
from .base import row_to_dict, rows_to_dicts

class AppointmentRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, appointment_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = """
        SELECT a.*, p.first_name || ' ' || p.last_name as patient_name, p.mrn as patient_mrn
        FROM APPOINTMENTS a
        JOIN PATIENTS p ON a.patient_id = p.patient_id
        WHERE a.appointment_id = :id
        """
        cursor.execute(query, {"id": appointment_id})
        return row_to_dict(cursor, cursor.fetchone())

    def list_appointments(self, date_str: Optional[str] = None, department: Optional[str] = None,
                           status: Optional[str] = None, patient_id: Optional[int] = None,
                           limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = """
        SELECT a.*, p.first_name || ' ' || p.last_name as patient_name, p.mrn as patient_mrn
        FROM APPOINTMENTS a
        JOIN PATIENTS p ON a.patient_id = p.patient_id
        WHERE 1=1
        """
        params: Dict[str, Any] = {}
        if date_str:
            if self.conn.dialect == "sqlite":
                query += " AND DATE(a.appointment_time) = :date_str"
            else:
                query += " AND TRUNC(CAST(a.appointment_time AS DATE)) = TO_DATE(:date_str, 'YYYY-MM-DD')"
            params["date_str"] = date_str
        if department:
            query += " AND a.department = :department"
            params["department"] = department
        if status:
            query += " AND a.status = :status"
            params["status"] = status
        if patient_id:
            query += " AND a.patient_id = :patient_id"
            params["patient_id"] = patient_id

        query += " ORDER BY a.appointment_time ASC LIMIT :limit OFFSET :offset" if self.conn.dialect == "sqlite" else \
                 " ORDER BY a.appointment_time ASC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        params["limit"] = limit
        params["offset"] = offset

        cursor.execute(query, params)
        return rows_to_dicts(cursor, cursor.fetchall())

    def count_appointments(self, date_str: Optional[str] = None, department: Optional[str] = None,
                           status: Optional[str] = None, patient_id: Optional[int] = None) -> int:
        cursor = self.conn.cursor()
        query = "SELECT COUNT(*) FROM APPOINTMENTS a WHERE 1=1"
        params: Dict[str, Any] = {}
        if date_str:
            if self.conn.dialect == "sqlite":
                query += " AND DATE(a.appointment_time) = :date_str"
            else:
                query += " AND TRUNC(CAST(a.appointment_time AS DATE)) = TO_DATE(:date_str, 'YYYY-MM-DD')"
            params["date_str"] = date_str
        if department:
            query += " AND a.department = :department"
            params["department"] = department
        if status:
            query += " AND a.status = :status"
            params["status"] = status
        if patient_id:
            query += " AND a.patient_id = :patient_id"
            params["patient_id"] = patient_id
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row[0] if row else 0

    def create(self, data: Dict[str, Any]) -> int:
        cursor = self.conn.cursor()
        if self.conn.dialect == "sqlite":
            query = """
            INSERT INTO APPOINTMENTS (patient_id, appointment_time, appointment_type, department, provider_name, status)
            VALUES (:patient_id, :appointment_time, :appointment_type, :department, :provider_name, 'SCHEDULED')
            """
            cursor.execute(query, data)
            return cursor.lastrowid
        else:
            cursor.execute("""
            INSERT INTO APPOINTMENTS (patient_id, appointment_time, appointment_type, department, provider_name, status)
            VALUES (:patient_id, TO_TIMESTAMP_TZ(:appointment_time, 'YYYY-MM-DD"T"HH24:MI:SS TZR'), :appointment_type, :department, :provider_name, 'SCHEDULED')
            RETURNING appointment_id INTO :appointment_id
            """, {**data, "appointment_id": cursor.var(int)})
            return cursor.getvar("appointment_id")

    def update_status(self, appointment_id: int, new_status: str, check_in_time: Optional[str] = None, cancel_reason: Optional[str] = None) -> None:
        cursor = self.conn.cursor()
        params = {"id": appointment_id, "status": new_status}
        set_parts = ["status = :status"]
        if check_in_time:
            set_parts.append("check_in_time = :check_in_time")
            params["check_in_time"] = check_in_time
        if cancel_reason:
            set_parts.append("cancel_reason = :cancel_reason")
            params["cancel_reason"] = cancel_reason

        query = f"UPDATE APPOINTMENTS SET {', '.join(set_parts)} WHERE appointment_id = :id"
        cursor.execute(query, params)

    def reschedule(self, appointment_id: int, new_time: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE APPOINTMENTS SET appointment_time = :new_time WHERE appointment_id = :id",
                       {"new_time": new_time, "id": appointment_id})
