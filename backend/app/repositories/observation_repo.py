from typing import Optional, List, Dict, Any
from .base import row_to_dict, rows_to_dicts

class ObservationRepository:
    def __init__(self, conn):
        self.conn = conn

    def list_by_encounter(self, encounter_id: int) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM OBSERVATIONS WHERE encounter_id = :id ORDER BY observation_time DESC",
                       {"id": encounter_id})
        return rows_to_dicts(cursor, cursor.fetchall())

    def list_by_patient(self, patient_id: int) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM OBSERVATIONS WHERE patient_id = :id ORDER BY observation_time DESC",
                       {"id": patient_id})
        return rows_to_dicts(cursor, cursor.fetchall())

    def create(self, data: Dict[str, Any]) -> int:
        cursor = self.conn.cursor()
        if self.conn.dialect == "sqlite":
            query = """
            INSERT INTO OBSERVATIONS (encounter_id, patient_id, observation_type, observation_code, value_numeric, value_text, unit, source, status)
            VALUES (:encounter_id, :patient_id, :observation_type, :observation_code, :value_numeric, :value_text, :unit, :source, 'FINAL')
            """
            cursor.execute(query, data)
            return cursor.lastrowid
        else:
            cursor.execute("""
            INSERT INTO OBSERVATIONS (encounter_id, patient_id, observation_type, observation_code, value_numeric, value_text, unit, source, status)
            VALUES (:encounter_id, :patient_id, :observation_type, :observation_code, :value_numeric, :value_text, :unit, :source, 'FINAL')
            RETURNING observation_id INTO :obs_id
            """, {**data, "obs_id": cursor.var(int)})
            return cursor.getvar("obs_id")
