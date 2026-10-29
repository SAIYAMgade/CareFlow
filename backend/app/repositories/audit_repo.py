from typing import Optional, List, Dict, Any
import json
import uuid
from .base import row_to_dict, rows_to_dicts

class AuditRepository:
    def __init__(self, conn):
        self.conn = conn

    def log_audit(self, entity_type: str, entity_id: int, action: str, actor: str,
                  previous_state: Optional[Any] = None, new_state: Optional[Any] = None,
                  reason: Optional[str] = None) -> None:
        cursor = self.conn.cursor()
        prev_str = json.dumps(previous_state) if isinstance(previous_state, dict) else (str(previous_state) if previous_state else None)
        new_str = json.dumps(new_state) if isinstance(new_state, dict) else (str(new_state) if new_state else None)
        corr_id = str(uuid.uuid4())
        
        cursor.execute("""
        INSERT INTO AUDIT_LOG (entity_type, entity_id, action, actor, previous_state, new_state, correlation_id, reason)
        VALUES (:entity_type, :entity_id, :action, :actor, :previous_state, :new_state, :correlation_id, :reason)
        """, {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "actor": actor,
            "previous_state": prev_str,
            "new_state": new_str,
            "correlation_id": corr_id,
            "reason": reason
        })

    def log_status_history(self, entity_type: str, entity_id: int, from_status: Optional[str],
                           to_status: str, actor: str, reason: Optional[str] = None) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO STATUS_HISTORY (entity_type, entity_id, from_status, to_status, actor, reason)
        VALUES (:entity_type, :entity_id, :from_status, :to_status, :actor, :reason)
        """, {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "from_status": from_status,
            "to_status": to_status,
            "actor": actor,
            "reason": reason
        })

    def list_audit_logs(self, entity_type: Optional[str] = None, entity_id: Optional[int] = None,
                        actor: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM AUDIT_LOG WHERE 1=1"
        params: Dict[str, Any] = {}
        if entity_type:
            query += " AND entity_type = :entity_type"
            params["entity_type"] = entity_type
        if entity_id:
            query += " AND entity_id = :entity_id"
            params["entity_id"] = entity_id
        if actor:
            query += " AND actor = :actor"
            params["actor"] = actor

        query += " ORDER BY audit_id DESC LIMIT :limit OFFSET :offset" if self.conn.dialect == "sqlite" else \
                 " ORDER BY audit_id DESC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        params["limit"] = limit
        params["offset"] = offset

        cursor.execute(query, params)
        return rows_to_dicts(cursor, cursor.fetchall())

    def count_audit_logs(self, entity_type: Optional[str] = None, entity_id: Optional[int] = None,
                         actor: Optional[str] = None) -> int:
        cursor = self.conn.cursor()
        query = "SELECT COUNT(*) FROM AUDIT_LOG WHERE 1=1"
        params: Dict[str, Any] = {}
        if entity_type:
            query += " AND entity_type = :entity_type"
            params["entity_type"] = entity_type
        if entity_id:
            query += " AND entity_id = :entity_id"
            params["entity_id"] = entity_id
        if actor:
            query += " AND actor = :actor"
            params["actor"] = actor
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row[0] if row else 0

    def list_status_history(self, entity_type: str, entity_id: int) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT * FROM STATUS_HISTORY
        WHERE entity_type = :entity_type AND entity_id = :entity_id
        ORDER BY history_id ASC
        """, {"entity_type": entity_type, "entity_id": entity_id})
        return rows_to_dicts(cursor, cursor.fetchall())
