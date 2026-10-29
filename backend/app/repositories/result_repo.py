from typing import Optional, List, Dict, Any
from .base import row_to_dict, rows_to_dicts

class ResultRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, result_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = """
        SELECT r.*, o.order_code, o.order_name, p.first_name || ' ' || p.last_name as patient_name, p.mrn as patient_mrn, e.department
        FROM RESULTS r
        JOIN ORDERS o ON r.order_id = o.order_id
        JOIN PATIENTS p ON o.patient_id = p.patient_id
        JOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id
        WHERE r.result_id = :id
        """
        cursor.execute(query, {"id": result_id})
        return row_to_dict(cursor, cursor.fetchone())

    def get_by_order_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = """
        SELECT r.*, o.order_code, o.order_name, p.first_name || ' ' || p.last_name as patient_name, p.mrn as patient_mrn, e.department
        FROM RESULTS r
        JOIN ORDERS o ON r.order_id = o.order_id
        JOIN PATIENTS p ON o.patient_id = p.patient_id
        JOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id
        WHERE r.order_id = :order_id
        """
        cursor.execute(query, {"order_id": order_id})
        return row_to_dict(cursor, cursor.fetchone())

    def list_results(self, result_status: Optional[str] = None, abnormal_only: bool = False,
                     limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = """
        SELECT r.*, o.order_code, o.order_name, p.first_name || ' ' || p.last_name as patient_name, p.mrn as patient_mrn, e.department
        FROM RESULTS r
        JOIN ORDERS o ON r.order_id = o.order_id
        JOIN PATIENTS p ON o.patient_id = p.patient_id
        JOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id
        WHERE 1=1
        """
        params: Dict[str, Any] = {}
        if result_status:
            query += " AND r.result_status = :status"
            params["status"] = result_status
        if abnormal_only:
            query += " AND r.abnormal_flag IN ('HIGH', 'LOW', 'CRITICAL')"

        query += " ORDER BY r.result_time DESC LIMIT :limit OFFSET :offset" if self.conn.dialect == "sqlite" else \
                 " ORDER BY r.result_time DESC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        params["limit"] = limit
        params["offset"] = offset

        cursor.execute(query, params)
        return rows_to_dicts(cursor, cursor.fetchall())

    def count_results(self, result_status: Optional[str] = None, abnormal_only: bool = False) -> int:
        cursor = self.conn.cursor()
        query = "SELECT COUNT(*) FROM RESULTS r WHERE 1=1"
        params: Dict[str, Any] = {}
        if result_status:
            query += " AND r.result_status = :status"
            params["status"] = result_status
        if abnormal_only:
            query += " AND r.abnormal_flag IN ('HIGH', 'LOW', 'CRITICAL')"
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row[0] if row else 0

    def create(self, data: Dict[str, Any]) -> int:
        cursor = self.conn.cursor()
        if self.conn.dialect == "sqlite":
            query = """
            INSERT INTO RESULTS (order_id, result_value, reference_range, unit, abnormal_flag, result_status)
            VALUES (:order_id, :result_value, :reference_range, :unit, :abnormal_flag, 'PENDING_REVIEW')
            """
            cursor.execute(query, data)
            return cursor.lastrowid
        else:
            cursor.execute("""
            INSERT INTO RESULTS (order_id, result_value, reference_range, unit, abnormal_flag, result_status)
            VALUES (:order_id, :result_value, :reference_range, :unit, :abnormal_flag, 'PENDING_REVIEW')
            RETURNING result_id INTO :result_id
            """, {**data, "result_id": cursor.var(int)})
            return cursor.getvar("result_id")

    def review_result(self, result_id: int, reviewer: str, reviewed_at: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
        UPDATE RESULTS 
        SET result_status = 'REVIEWED', reviewed_by = :reviewer, reviewed_at = :reviewed_at
        WHERE result_id = :id
        """, {"reviewer": reviewer, "reviewed_at": reviewed_at, "id": result_id})
