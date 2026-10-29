from typing import Optional, List, Dict, Any
from .base import row_to_dict, rows_to_dicts

class DataQualityRepository:
    def __init__(self, conn):
        self.conn = conn

    def list_issues(self, status: Optional[str] = None, severity: Optional[str] = None,
                    entity: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM DATA_QUALITY_ISSUES WHERE 1=1"
        params: Dict[str, Any] = {}
        if status:
            query += " AND resolution_status = :status"
            params["status"] = status
        if severity:
            query += " AND severity = :severity"
            params["severity"] = severity
        if entity:
            query += " AND affected_entity = :entity"
            params["entity"] = entity

        query += " ORDER BY issue_id DESC LIMIT :limit OFFSET :offset" if self.conn.dialect == "sqlite" else \
                 " ORDER BY issue_id DESC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        params["limit"] = limit
        params["offset"] = offset

        cursor.execute(query, params)
        return rows_to_dicts(cursor, cursor.fetchall())

    def count_issues(self, status: Optional[str] = None, severity: Optional[str] = None, entity: Optional[str] = None) -> int:
        cursor = self.conn.cursor()
        query = "SELECT COUNT(*) FROM DATA_QUALITY_ISSUES WHERE 1=1"
        params: Dict[str, Any] = {}
        if status:
            query += " AND resolution_status = :status"
            params["status"] = status
        if severity:
            query += " AND severity = :severity"
            params["severity"] = severity
        if entity:
            query += " AND affected_entity = :entity"
            params["entity"] = entity
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row[0] if row else 0

    def get_by_id(self, issue_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM DATA_QUALITY_ISSUES WHERE issue_id = :id", {"id": issue_id})
        return row_to_dict(cursor, cursor.fetchone())

    def record_issue(self, rule_code: str, severity: str, affected_entity: str,
                     entity_id: int, description: str, steps: str) -> None:
        cursor = self.conn.cursor()
        # Check if already open
        cursor.execute("""
        SELECT issue_id FROM DATA_QUALITY_ISSUES 
        WHERE rule_code = :rule_code AND entity_id = :entity_id AND resolution_status = 'OPEN'
        """, {"rule_code": rule_code, "entity_id": entity_id})
        if cursor.fetchone():
            return # already logged
        
        cursor.execute("""
        INSERT INTO DATA_QUALITY_ISSUES (rule_code, severity, affected_entity, entity_id, description, investigation_steps, resolution_status)
        VALUES (:rule_code, :severity, :affected_entity, :entity_id, :description, :steps, 'OPEN')
        """, {
            "rule_code": rule_code,
            "severity": severity,
            "affected_entity": affected_entity,
            "entity_id": entity_id,
            "description": description,
            "steps": steps
        })

    def resolve_issue(self, issue_id: int, resolved_by: str, status: str, notes: str, resolved_at: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
        UPDATE DATA_QUALITY_ISSUES
        SET resolution_status = :status, resolved_by = :resolved_by, remediation_notes = :notes, resolved_at = :resolved_at
        WHERE issue_id = :id
        """, {"status": status, "resolved_by": resolved_by, "notes": notes, "resolved_at": resolved_at, "id": issue_id})
