from typing import Optional, List, Dict, Any
from .base import row_to_dict, rows_to_dicts

class EncounterRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, encounter_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = """
        SELECT e.*, p.first_name || ' ' || p.last_name as patient_name, p.mrn as patient_mrn
        FROM ENCOUNTERS e
        JOIN PATIENTS p ON e.patient_id = p.patient_id
        WHERE e.encounter_id = :id
        """
        cursor.execute(query, {"id": encounter_id})
        return row_to_dict(cursor, cursor.fetchone())

    def list_encounters(self, patient_id: Optional[int] = None, department: Optional[str] = None,
                        status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = """
        SELECT e.*, p.first_name || ' ' || p.last_name as patient_name, p.mrn as patient_mrn
        FROM ENCOUNTERS e
        JOIN PATIENTS p ON e.patient_id = p.patient_id
        WHERE 1=1
        """
        params: Dict[str, Any] = {}
        if patient_id:
            query += " AND e.patient_id = :patient_id"
            params["patient_id"] = patient_id
        if department:
            query += " AND e.department = :department"
            params["department"] = department
        if status:
            query += " AND e.status = :status"
            params["status"] = status

        query += " ORDER BY e.start_time DESC LIMIT :limit OFFSET :offset" if self.conn.dialect == "sqlite" else \
                 " ORDER BY e.start_time DESC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        params["limit"] = limit
        params["offset"] = offset

        cursor.execute(query, params)
        return rows_to_dicts(cursor, cursor.fetchall())

    def count_encounters(self, patient_id: Optional[int] = None, department: Optional[str] = None,
                         status: Optional[str] = None) -> int:
        cursor = self.conn.cursor()
        query = "SELECT COUNT(*) FROM ENCOUNTERS e WHERE 1=1"
        params: Dict[str, Any] = {}
        if patient_id:
            query += " AND e.patient_id = :patient_id"
            params["patient_id"] = patient_id
        if department:
            query += " AND e.department = :department"
            params["department"] = department
        if status:
            query += " AND e.status = :status"
            params["status"] = status
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row[0] if row else 0

    def create(self, data: Dict[str, Any]) -> int:
        cursor = self.conn.cursor()
        if self.conn.dialect == "sqlite":
            query = """
            INSERT INTO ENCOUNTERS (patient_id, appointment_id, encounter_type, department, provider_name, status, chief_complaint, clinical_notes)
            VALUES (:patient_id, :appointment_id, :encounter_type, :department, :provider_name, 'OPEN', :chief_complaint, :clinical_notes)
            """
            cursor.execute(query, data)
            return cursor.lastrowid
        else:
            cursor.execute("""
            INSERT INTO ENCOUNTERS (patient_id, appointment_id, encounter_type, department, provider_name, status, chief_complaint, clinical_notes)
            VALUES (:patient_id, :appointment_id, :encounter_type, :department, :provider_name, 'OPEN', :chief_complaint, :clinical_notes)
            RETURNING encounter_id INTO :encounter_id
            """, {**data, "encounter_id": cursor.var(int)})
            return cursor.getvar("encounter_id")

    def update_status(self, encounter_id: int, new_status: str, end_time: Optional[str] = None, notes: Optional[str] = None) -> None:
        cursor = self.conn.cursor()
        params = {"id": encounter_id, "status": new_status}
        set_parts = ["status = :status"]
        if end_time:
            set_parts.append("end_time = :end_time")
            params["end_time"] = end_time
        if notes:
            set_parts.append("clinical_notes = :notes")
            params["notes"] = notes

        query = f"UPDATE ENCOUNTERS SET {', '.join(set_parts)} WHERE encounter_id = :id"
        cursor.execute(query, params)

    def update_notes(self, encounter_id: int, notes: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE ENCOUNTERS SET clinical_notes = :notes WHERE encounter_id = :id",
                       {"notes": notes, "id": encounter_id})
