from typing import Any, List, Dict, Optional

def row_to_dict(cursor, row) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    # If sqlite3.Row
    if hasattr(row, "keys"):
        return {k.lower(): row[k] for k in row.keys()}
    # If Oracle tuple
    if cursor.description:
        col_names = [col[0].lower() for col in cursor.description]
        return dict(zip(col_names, row))
    return {}

def rows_to_dicts(cursor, rows) -> List[Dict[str, Any]]:
    if not rows:
        return []
    return [row_to_dict(cursor, r) for r in rows if r is not None]
