from typing import Optional, List, Dict, Any
from .base import row_to_dict, rows_to_dicts

class OrderRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = """
        SELECT o.*, p.first_name || ' ' || p.last_name as patient_name, p.mrn as patient_mrn, e.department
        FROM ORDERS o
        JOIN PATIENTS p ON o.patient_id = p.patient_id
        JOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id
        WHERE o.order_id = :id
        """
        cursor.execute(query, {"id": order_id})
        return row_to_dict(cursor, cursor.fetchone())

    def list_orders(self, encounter_id: Optional[int] = None, patient_id: Optional[int] = None,
                    status: Optional[str] = None, priority: Optional[str] = None,
                    limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = """
        SELECT o.*, p.first_name || ' ' || p.last_name as patient_name, p.mrn as patient_mrn, e.department
        FROM ORDERS o
        JOIN PATIENTS p ON o.patient_id = p.patient_id
        JOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id
        WHERE 1=1
        """
        params: Dict[str, Any] = {}
        if encounter_id:
            query += " AND o.encounter_id = :encounter_id"
            params["encounter_id"] = encounter_id
        if patient_id:
            query += " AND o.patient_id = :patient_id"
            params["patient_id"] = patient_id
        if status:
            query += " AND o.order_status = :status"
            params["status"] = status
        if priority:
            query += " AND o.priority = :priority"
            params["priority"] = priority

        query += " ORDER BY o.ordered_at DESC LIMIT :limit OFFSET :offset" if self.conn.dialect == "sqlite" else \
                 " ORDER BY o.ordered_at DESC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        params["limit"] = limit
        params["offset"] = offset

        cursor.execute(query, params)
        return rows_to_dicts(cursor, cursor.fetchall())

    def count_orders(self, encounter_id: Optional[int] = None, patient_id: Optional[int] = None,
                     status: Optional[str] = None, priority: Optional[str] = None) -> int:
        cursor = self.conn.cursor()
        query = "SELECT COUNT(*) FROM ORDERS o WHERE 1=1"
        params: Dict[str, Any] = {}
        if encounter_id:
            query += " AND o.encounter_id = :encounter_id"
            params["encounter_id"] = encounter_id
        if patient_id:
            query += " AND o.patient_id = :patient_id"
            params["patient_id"] = patient_id
        if status:
            query += " AND o.order_status = :status"
            params["status"] = status
        if priority:
            query += " AND o.priority = :priority"
            params["priority"] = priority
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row[0] if row else 0

    def create(self, data: Dict[str, Any]) -> int:
        cursor = self.conn.cursor()
        if self.conn.dialect == "sqlite":
            query = """
            INSERT INTO ORDERS (encounter_id, patient_id, order_type, order_code, order_name, priority, ordered_by, order_status)
            VALUES (:encounter_id, :patient_id, :order_type, :order_code, :order_name, :priority, :ordered_by, 'ORDERED')
            """
            cursor.execute(query, data)
            return cursor.lastrowid
        else:
            cursor.execute("""
            INSERT INTO ORDERS (encounter_id, patient_id, order_type, order_code, order_name, priority, ordered_by, order_status)
            VALUES (:encounter_id, :patient_id, :order_type, :order_code, :order_name, :priority, :ordered_by, 'ORDERED')
            RETURNING order_id INTO :order_id
            """, {**data, "order_id": cursor.var(int)})
            return cursor.getvar("order_id")

    def complete_order(self, order_id: int, completed_at: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE ORDERS SET order_status = 'COMPLETED', completed_at = :completed_at WHERE order_id = :id",
                       {"completed_at": completed_at, "id": order_id})

    def count_pending_by_encounter(self, encounter_id: int) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT COUNT(*) FROM ORDERS
        WHERE encounter_id = :encounter_id AND order_status IN ('ORDERED', 'IN_PROGRESS')
        """, {"encounter_id": encounter_id})
        row = cursor.fetchone()
        return row[0] if row else 0
