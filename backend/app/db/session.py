import sqlite3
import os
from contextlib import contextmanager
from typing import Generator, Any
from ..core.config import settings
from ..core.logging import logger

# Conditional oracledb import
try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False

_oracle_pool = None

def get_oracle_pool():
    global _oracle_pool
    if not ORACLE_AVAILABLE:
        raise RuntimeError("python-oracledb is not installed.")
    if _oracle_pool is None:
        try:
            logger.info(f"Connecting to Oracle Database Free DSN: {settings.ORACLE_DSN} as {settings.ORACLE_USER}")
            _oracle_pool = oracledb.create_pool(
                user=settings.ORACLE_USER,
                password=settings.ORACLE_PASSWORD,
                dsn=settings.ORACLE_DSN,
                min=1,
                max=10,
                increment=1
            )
            logger.info("Oracle connection pool initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to create Oracle connection pool: {e}")
            raise
    return _oracle_pool

class DBConnectionWrapper:
    def __init__(self, raw_conn, dialect: str):
        self.raw_conn = raw_conn
        self.dialect = dialect

    def cursor(self):
        return self.raw_conn.cursor()

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        self.raw_conn.close()

@contextmanager
def get_db() -> Generator[DBConnectionWrapper, None, None]:
    """
    Context manager that yields a database connection wrapper.
    Supports rollback on unhandled exceptions and automatic close.
    """
    if settings.DATABASE_DIALECT.lower() == "oracle":
        pool = get_oracle_pool()
        raw_conn = pool.acquire()
        wrapper = DBConnectionWrapper(raw_conn, dialect="oracle")
        try:
            yield wrapper
        except Exception:
            raw_conn.rollback()
            raise
        finally:
            pool.release(raw_conn)
    else:
        # SQLite Standalone/Fallback Mode
        db_path = os.path.abspath(settings.SQLITE_PATH)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        raw_conn = sqlite3.connect(db_path, timeout=30.0, detect_types=sqlite3.PARSE_DECLTYPES)
        raw_conn.row_factory = sqlite3.Row
        raw_conn.execute("PRAGMA foreign_keys = ON;")
        wrapper = DBConnectionWrapper(raw_conn, dialect="sqlite")
        try:
            yield wrapper
        except Exception:
            raw_conn.rollback()
            raise
        finally:
            raw_conn.close()

def check_db_health() -> dict[str, Any]:
    """Health check ping for the configured database engine."""
    dialect = settings.DATABASE_DIALECT.lower()
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            if dialect == "oracle":
                cursor.execute("SELECT SYSTIMESTAMP, banner FROM v$version WHERE ROWNUM = 1")
                row = cursor.fetchone()
                return {
                    "status": "UP",
                    "dialect": "oracle",
                    "database_version": row[1] if row else "Oracle Database Free",
                    "server_time": str(row[0]) if row else None,
                    "connected": True
                }
            else:
                cursor.execute("SELECT datetime('now'), sqlite_version()")
                row = cursor.fetchone()
                return {
                    "status": "UP",
                    "dialect": "sqlite",
                    "database_version": f"SQLite {row[1]}" if row else "SQLite 3",
                    "server_time": row[0] if row else None,
                    "connected": True
                }
    except Exception as e:
        return {
            "status": "DOWN",
            "dialect": dialect,
            "error": str(e),
            "connected": False
        }
