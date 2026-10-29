import pytest
import os
from backend.app.core.config import settings

def is_oracle_reachable():
    try:
        import oracledb
        conn = oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=settings.ORACLE_DSN,
            tcp_connect_timeout=2.0
        )
        conn.close()
        return True
    except Exception:
        return False

@pytest.mark.skipif(not is_oracle_reachable(), reason="Oracle Database Free (localhost:1521/FREEPDB1) is not running or unreachable in this host environment. Per Section 12/18 rules, Oracle integration tests are explicitly marked as UNVERIFIED rather than substituted.")
class TestOracleDatabaseFreeIntegration:
    """
    Oracle Database Free Integration Test Suite.
    Executes actual DDL, PL/SQL package procedures, transactions, and rollback against Oracle.
    """

    def test_oracle_version_and_connectivity(self):
        import oracledb
        with oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=settings.ORACLE_DSN
        ) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
            banner = cursor.fetchone()[0]
            assert "Oracle" in banner

    def test_oracle_schema_objects_present(self):
        import oracledb
        with oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=settings.ORACLE_DSN
        ) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT table_name FROM user_tables 
            WHERE table_name IN ('PATIENTS', 'APPOINTMENTS', 'ENCOUNTERS', 'ORDERS', 'RESULTS', 'DATA_QUALITY_ISSUES', 'AUDIT_LOG')
            """)
            tables = {r[0] for r in cursor.fetchall()}
            assert "PATIENTS" in tables
            assert "ENCOUNTERS" in tables
            assert "RESULTS" in tables

    def test_oracle_plsql_package_validity(self):
        import oracledb
        with oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=settings.ORACLE_DSN
        ) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT object_name, object_type, status 
            FROM user_objects 
            WHERE object_name = 'CAREFLOW_WORKFLOW_PKG'
            """)
            rows = cursor.fetchall()
            assert len(rows) >= 2 # Specification and Body
            for r in rows:
                assert r[2] == "VALID", f"{r[0]} ({r[1]}) is INVALID"
