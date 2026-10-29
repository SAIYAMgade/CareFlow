from typing import Optional, List, Dict, Any
from .base import row_to_dict, rows_to_dicts

class PatientRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, patient_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM PATIENTS WHERE patient_id = :id", {"id": patient_id})
        return row_to_dict(cursor, cursor.fetchone())

    def get_by_mrn(self, mrn: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM PATIENTS WHERE mrn = :mrn", {"mrn": mrn})
        return row_to_dict(cursor, cursor.fetchone())

    def list_patients(self, search: Optional[str] = None, status: Optional[str] = None,
                      limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM PATIENTS WHERE 1=1"
        params: Dict[str, Any] = {}
        
        if search:
            query += " AND (UPPER(first_name) LIKE :search OR UPPER(last_name) LIKE :search OR UPPER(mrn) LIKE :search)"
            params["search"] = f"%{search.upper()}%"
        if status:
            query += " AND status = :status"
            params["status"] = status

        query += " ORDER BY patient_id DESC LIMIT :limit OFFSET :offset" if self.conn.dialect == "sqlite" else \
                 " ORDER BY patient_id DESC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        params["limit"] = limit
        params["offset"] = offset

        cursor.execute(query, params)
        return rows_to_dicts(cursor, cursor.fetchall())

    def count_patients(self, search: Optional[str] = None, status: Optional[str] = None) -> int:
        cursor = self.conn.cursor()
        query = "SELECT COUNT(*) as cnt FROM PATIENTS WHERE 1=1"
        params: Dict[str, Any] = {}
        if search:
            query += " AND (UPPER(first_name) LIKE :search OR UPPER(last_name) LIKE :search OR UPPER(mrn) LIKE :search)"
            params["search"] = f"%{search.upper()}%"
        if status:
            query += " AND status = :status"
            params["status"] = status
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row[0] if row else 0

    def create(self, data: Dict[str, Any]) -> int:
        cursor = self.conn.cursor()
        if self.conn.dialect == "sqlite":
            query = """
            INSERT INTO PATIENTS (mrn, first_name, last_name, date_of_birth, gender, phone, email, address, status)
            VALUES (:mrn, :first_name, :last_name, :date_of_birth, :gender, :phone, :email, :address, :status)
            """
            cursor.execute(query, data)
            return cursor.lastrowid
        else:
            # Oracle
            cursor.execute("""
            INSERT INTO PATIENTS (mrn, first_name, last_name, date_of_birth, gender, phone, email, address, status)
            VALUES (:mrn, :first_name, :last_name, TO_DATE(:date_of_birth, 'YYYY-MM-DD'), :gender, :phone, :email, :address, :status)
            RETURNING patient_id INTO :patient_id
            """, {**data, "patient_id": cursor.var(int)})
            return cursor.getvar("patient_id")

    def update(self, patient_id: int, updates: Dict[str, Any]) -> None:
        if not updates:
            return
        cursor = self.conn.cursor()
        set_clauses = []
        params = {"patient_id": patient_id}
        for k, v in updates.items():
            set_clauses.append(f"{k} = :{k}")
            params[k] = v
        
        query = f"UPDATE PATIENTS SET {', '.join(set_clauses)} WHERE patient_id = :patient_id"
        cursor.execute(query, params)
