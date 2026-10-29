# CareFlow Troubleshooting & Diagnostic Guide

This guide details common operational and database errors encountered when running CareFlow against **Oracle Database Free** and local environments.

---

## 1. Oracle Database Connection Errors

### A. `ORA-12541: TNS:no listener` / Connection Refused
- **Symptom:** Backend fails to connect with message `DPY-4000: cannot connect to host localhost port 1521`.
- **Root Cause:** The Oracle listener is not running or the Docker container `careflow-oracle-free` has not finished booting up.
- **Diagnostic Steps:**
  ```bash
  # Check container status
  docker ps -a
  
  # Check Oracle container startup logs
  docker logs -f careflow-oracle-free
  ```
- **Resolution:**
  1. Ensure container is running: `docker start careflow-oracle-free`.
  2. Wait until the container logs show: `DATABASE IS READY TO USE!`.
  3. Verify port mapping: `netstat -an | findstr 1521`.

---

### B. `ORA-01017: invalid username/password; logon denied`
- **Symptom:** Authentication fails during connection pool initialization.
- **Root Cause:** The password or user does not match the configured environment variables.
- **Resolution:**
  1. Verify `.env` settings:
     ```env
     ORACLE_USER=careflow_admin
     ORACLE_PASSWORD=CareFlowSecretPass2026#
     ORACLE_DSN=localhost:1521/FREEPDB1
     ```
  2. Connect as `SYSDBA` via SQL*Plus or SQLcl:
     ```sql
     sqlplus sys/CareFlowSecretPass2026#@localhost:1521/FREEPDB1 as sysdba
     ALTER USER careflow_admin IDENTIFIED BY "CareFlowSecretPass2026#";
     ```

---

### C. `ORA-00001: unique constraint (UQ_PATIENTS_MRN) violated`
- **Symptom:** HTTP 400 `DATA_INTEGRITY_VIOLATION` returned during patient registration.
- **Root Cause:** Attempting to insert a patient with an MRN that already exists in `PATIENTS`.
- **Resolution:**
  - In CareFlow, MRNs are immutable and unique. If registering a new patient, leave the `mrn` field blank to let the system generate a fresh unique sequence `MRN-YYYY-XXXXX`.

---

### D. `ORA-20003: Encounter cannot be completed: pending orders remain`
- **Symptom:** HTTP 409 `INVALID_STATE_TRANSITION` when attempting to mark an encounter as `COMPLETED`.
- **Root Cause:** Enforced by PL/SQL package `careflow_workflow_pkg.complete_encounter`. One or more laboratory orders attached to this encounter remain in `ORDERED` or `IN_PROGRESS` status.
- **Resolution:**
  1. Navigate to **Orders & Results**.
  2. Complete outstanding lab orders by posting their results, or cancel the test.
  3. Once all orders reach `COMPLETED` or `CANCELLED`, retry completing the encounter.

---

## 2. API & Python Environment Diagnostics

### A. Missing `oracledb` or C Compiler Issues on Windows
- `python-oracledb` installs as a precompiled binary wheel in Thin mode. Thin mode requires **no Oracle Instant Client** or C compiler installed.
- Verify installation:
  ```bash
  python -c "import oracledb; print(oracledb.__version__)"
  ```

### B. Switching to Standalone Fallback Engine
- If Docker or Oracle Database Free cannot be run on the host machine:
  1. Edit `.env`:
     ```env
     DATABASE_DIALECT=sqlite
     ```
  2. Re-seed the local database:
     ```bash
     python scripts/seed_data.py
     ```
  3. Start the application:
     ```bash
     uvicorn backend.app.main:app --reload --port 8000
     ```
