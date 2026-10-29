import os
from .session import get_db
from ..core.config import settings
from ..core.logging import logger

SQLITE_SCHEMA = """
-- ============================================================================
-- CareFlow Healthcare Operations Platform
-- SQLite Compatible Schema (Standalone / Local Demonstration Mode)
-- ============================================================================

DROP TABLE IF EXISTS STATUS_HISTORY;
DROP TABLE IF EXISTS AUDIT_LOG;
DROP TABLE IF EXISTS DATA_QUALITY_ISSUES;
DROP TABLE IF EXISTS RESULTS;
DROP TABLE IF EXISTS ORDERS;
DROP TABLE IF EXISTS OBSERVATIONS;
DROP TABLE IF EXISTS ENCOUNTERS;
DROP TABLE IF EXISTS APPOINTMENTS;
DROP TABLE IF EXISTS PATIENTS;

CREATE TABLE PATIENTS (
    patient_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    mrn             TEXT NOT NULL UNIQUE,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    date_of_birth   TEXT NOT NULL,
    gender          TEXT DEFAULT 'UNKNOWN' CHECK(gender IN ('FEMALE', 'MALE', 'OTHER', 'UNKNOWN')),
    phone           TEXT,
    email           TEXT,
    address         TEXT,
    status          TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'INACTIVE', 'MERGED')),
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at      TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE APPOINTMENTS (
    appointment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id       INTEGER NOT NULL,
    appointment_time TEXT NOT NULL,
    appointment_type TEXT DEFAULT 'FOLLOW_UP' NOT NULL,
    department       TEXT NOT NULL,
    provider_name    TEXT NOT NULL,
    status           TEXT DEFAULT 'SCHEDULED' NOT NULL CHECK(status IN (
        'SCHEDULED', 'CHECKED_IN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW'
    )),
    check_in_time    TEXT,
    cancel_reason    TEXT,
    created_at       TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at       TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id)
);

CREATE TABLE ENCOUNTERS (
    encounter_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    appointment_id  INTEGER,
    encounter_type  TEXT DEFAULT 'OUTPATIENT' NOT NULL,
    department      TEXT NOT NULL,
    provider_name   TEXT NOT NULL,
    status          TEXT DEFAULT 'OPEN' NOT NULL CHECK(status IN (
        'OPEN', 'IN_PROGRESS', 'AWAITING_RESULTS', 'COMPLETED', 'CANCELLED'
    )),
    start_time      TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    end_time        TEXT,
    chief_complaint TEXT,
    clinical_notes  TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at      TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id),
    FOREIGN KEY (appointment_id) REFERENCES APPOINTMENTS(appointment_id)
);

CREATE TABLE OBSERVATIONS (
    observation_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id     INTEGER NOT NULL,
    patient_id       INTEGER NOT NULL,
    observation_type TEXT NOT NULL,
    observation_code TEXT NOT NULL,
    value_numeric    REAL,
    value_text       TEXT,
    unit             TEXT,
    observation_time TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status           TEXT DEFAULT 'FINAL' NOT NULL CHECK(status IN ('PRELIMINARY', 'FINAL', 'AMENDED', 'CANCELLED')),
    source           TEXT DEFAULT 'CLINICAL_TRIAGE' NOT NULL,
    FOREIGN KEY (encounter_id) REFERENCES ENCOUNTERS(encounter_id),
    FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id)
);

CREATE TABLE ORDERS (
    order_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id  INTEGER NOT NULL,
    patient_id    INTEGER NOT NULL,
    order_type    TEXT DEFAULT 'LABORATORY' NOT NULL,
    order_code    TEXT NOT NULL,
    order_name    TEXT NOT NULL,
    order_status  TEXT DEFAULT 'ORDERED' NOT NULL CHECK(order_status IN ('ORDERED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
    priority      TEXT DEFAULT 'ROUTINE' NOT NULL CHECK(priority IN ('STAT', 'URGENT', 'ROUTINE')),
    ordered_by    TEXT NOT NULL,
    ordered_at    TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at  TEXT,
    FOREIGN KEY (encounter_id) REFERENCES ENCOUNTERS(encounter_id),
    FOREIGN KEY (patient_id) REFERENCES PATIENTS(patient_id)
);

CREATE TABLE RESULTS (
    result_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL UNIQUE,
    result_value    TEXT NOT NULL,
    reference_range TEXT,
    unit            TEXT,
    abnormal_flag   TEXT DEFAULT 'NORMAL' NOT NULL CHECK(abnormal_flag IN ('NORMAL', 'HIGH', 'LOW', 'CRITICAL')),
    result_status   TEXT DEFAULT 'PENDING_REVIEW' NOT NULL CHECK(result_status IN ('PENDING_REVIEW', 'REVIEWED', 'AMENDED')),
    reviewed_by     TEXT,
    reviewed_at     TEXT,
    result_time     TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (order_id) REFERENCES ORDERS(order_id)
);

CREATE TABLE DATA_QUALITY_ISSUES (
    issue_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code           TEXT NOT NULL,
    severity            TEXT NOT NULL CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    affected_entity     TEXT NOT NULL,
    entity_id           INTEGER NOT NULL,
    detection_time      TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    description         TEXT NOT NULL,
    investigation_steps TEXT NOT NULL,
    resolution_status   TEXT DEFAULT 'OPEN' NOT NULL CHECK(resolution_status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE')),
    resolved_by         TEXT,
    resolved_at         TEXT,
    remediation_notes   TEXT
);

CREATE TABLE AUDIT_LOG (
    audit_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type     TEXT NOT NULL,
    entity_id       INTEGER NOT NULL,
    action          TEXT NOT NULL,
    actor           TEXT NOT NULL,
    previous_state  TEXT,
    new_state       TEXT,
    correlation_id  TEXT,
    reason          TEXT,
    changed_at      TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE STATUS_HISTORY (
    history_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type     TEXT NOT NULL,
    entity_id       INTEGER NOT NULL,
    from_status     TEXT,
    to_status       TEXT NOT NULL,
    actor           TEXT NOT NULL,
    reason          TEXT,
    changed_at      TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes
CREATE INDEX idx_patients_name ON PATIENTS (last_name, first_name);
CREATE INDEX idx_appts_time_dept ON APPOINTMENTS (appointment_time, department, status);
CREATE INDEX idx_enc_patient ON ENCOUNTERS (patient_id, status);
CREATE INDEX idx_enc_appt ON ENCOUNTERS (appointment_id);
CREATE INDEX idx_ord_encounter ON ORDERS (encounter_id, order_status);
CREATE INDEX idx_ord_status ON ORDERS (order_status, ordered_at);
CREATE INDEX idx_res_status ON RESULTS (result_status, abnormal_flag);
CREATE INDEX idx_dq_status ON DATA_QUALITY_ISSUES (resolution_status, severity);
CREATE INDEX idx_audit_time ON AUDIT_LOG (entity_type, entity_id, changed_at);
"""

def init_database():
    """Initializes schema based on configured database dialect."""
    dialect = settings.DATABASE_DIALECT.lower()
    logger.info(f"Initializing database for dialect: {dialect}")
    
    with get_db() as conn:
        cursor = conn.cursor()
        if dialect == "sqlite":
            cursor.executescript(SQLITE_SCHEMA)
            conn.commit()
            logger.info("SQLite database schema initialized successfully.")
        else:
            # Oracle Database Free Initialization
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../database"))
            schema_file = os.path.join(base_dir, "schema/01_tables_and_constraints.sql")
            index_file = os.path.join(base_dir, "schema/02_indexes.sql")
            pkg_spec = os.path.join(base_dir, "packages/careflow_workflow_pkg.pks")
            pkg_body = os.path.join(base_dir, "packages/careflow_workflow_pkg.pkb")
            views_file = os.path.join(base_dir, "views/careflow_views.sql")
            
            for file_path in [schema_file, index_file, pkg_spec, pkg_body, views_file]:
                if os.path.exists(file_path):
                    logger.info(f"Executing Oracle DDL script: {file_path}")
                    with open(file_path, "r", encoding="utf-8") as f:
                        sql_content = f.read()
                    # Execute PL/SQL or split statements
                    # Oracle scripts with '/' blocks or statements
                    # For oracledb, procedures/packages are executed as single blocks
                    try:
                        cursor.execute(sql_content)
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Error executing {file_path}: {e}")
                        raise
            logger.info("Oracle database schema and PL/SQL packages initialized.")

if __name__ == "__main__":
    init_database()
