# CareFlow: Healthcare Workflow, Clinical Data Management & Reporting Platform

[![CI Pipeline](https://github.com/SAIYAMgade/CareFlow/actions/workflows/ci.yml/badge.svg)](https://github.com/SAIYAMgade/CareFlow/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20TypeScript-61DAFB.svg)](https://reactjs.org/)
[![Oracle Database](https://img.shields.io/badge/Database-Oracle%20Database%20Free%2023ai-F80000.svg)](https://www.oracle.com/database/free/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **IMPORTANT DISCLAIMER:** CareFlow is an educational healthcare operational simulation platform built for technical portfolio demonstration with **100% synthetic data**. It is not a certified electronic health record (EHR), diagnostic medical software, or production healthcare system.

---

## 1. Visual Platform Overview

<p align="center">
  <img src="assets/careflow_dashboard_preview.svg" alt="CareFlow Clinical Operations Dashboard" width="100%">
</p>

### Operational KPI Summary Table (Derived from Persisted Records)

| Operational Metric | Live Database Query Source | Business Meaning & Triage Role |
| :--- | :--- | :--- |
| **Today's Appointments** | `COUNT(*) FROM APPOINTMENTS WHERE appointment_time = TODAY` | Total patient volume scheduled across all 5 clinical departments |
| **Patients Checked In** | `COUNT(*) FROM APPOINTMENTS WHERE status = 'CHECKED_IN'` | Patients who physically arrived at clinic reception kiosks |
| **Patients Waiting** | `COUNT(*) FROM APPOINTMENTS a WHERE status = 'CHECKED_IN' AND NOT EXISTS (active encounter)` | Patients queued in the clinic waiting lounge awaiting triage |
| **Encounters In Progress** | `COUNT(*) FROM ENCOUNTERS WHERE status IN ('OPEN', 'IN_PROGRESS', 'AWAITING_RESULTS')` | Active patient consultations and clinical evaluations currently underway |
| **Encounters Completed** | `COUNT(*) FROM ENCOUNTERS WHERE status = 'COMPLETED'` | Concluded patient visits with physician documentation signed off |
| **Orders Awaiting Results** | `COUNT(*) FROM ORDERS WHERE order_status IN ('ORDERED', 'IN_PROGRESS')` | Diagnostic laboratory backlog pending specimen processing |
| **Results Awaiting Review** | `COUNT(*) FROM RESULTS WHERE result_status = 'PENDING_REVIEW'` | Critical, abnormal, or normal lab results requiring physician signoff |
| **Data Quality Exceptions** | `COUNT(*) FROM DATA_QUALITY_ISSUES WHERE resolution_status = 'OPEN'` | Invariant anomalies flagged by the automated audit engine |

---

## 2. System Architecture

<p align="center">
  <img src="assets/careflow_architecture_diagram.svg" alt="CareFlow System Architecture" width="100%">
</p>

```mermaid
graph TD
    subgraph ClientTier ["Presentation Tier (React 18 + TypeScript + Vite)"]
        UI["Healthcare Operational Interface"]
        Tailwind["Tailwind CSS + Lucide Icons"]
    end

    subgraph APITier ["Application Tier (FastAPI + Pydantic v2)"]
        Router["REST Routers (/api)"]
        Schemas["Pydantic Data Contracts"]
        Services["Domain Services (Workflows & Safety Gates)"]
        Repo["Parameterized Repositories"]
    end

    subgraph DataTier ["Persistence Tier (Oracle Database Free 23ai)"]
        Schema["Relational Tables & Constraints"]
        PLSQL["CAREFLOW_WORKFLOW_PKG (PL/SQL)"]
        Views["Analytical Views"]
        Audit["AUDIT_LOG & STATUS_HISTORY"]
    end

    UI --> Router
    Router --> Schemas
    Schemas --> Services
    Services --> Repo
    Repo --> Schema
    Repo --> PLSQL
```

---

## 3. Clinical Workflow Lifecycle & Safety Gate

<p align="center">
  <img src="assets/careflow_workflow_lifecycle.svg" alt="CareFlow Clinical Workflow State Machine" width="100%">
</p>

### State Machine Transition Rules

| Transition Event | From State | Target State | Enforced Business Invariants & Integrity Gates |
| :--- | :--- | :--- | :--- |
| **Reception Check-In** | `SCHEDULED` | `CHECKED_IN` | **Atomic PL/SQL Transaction:** Records arrival timestamp `check_in_time = SYSTIMESTAMP` and auto-generates an initial `ENCOUNTER` record in `OPEN` status. Re-checking in an already arrived patient is rejected with HTTP 409. |
| **Clinical Consultation** | `OPEN` | `IN_PROGRESS` | Clinician opens exam room record and begins recording symptoms, vital signs, and diagnostic requisitions. |
| **Lab Requisition** | — | `ORDERED` | Places laboratory order (`CBC`, `BMP`, `LIPID`, `TSH`, `HBA1C`, `UA`). Can only be dispatched from active encounters. |
| **Encounter Signoff Gate** | `IN_PROGRESS` | `COMPLETED` | **Safety Enforcement Gate:** The system blocks visit completion with `ORA-20003` if any diagnostic order remains in `ORDERED` or `IN_PROGRESS` status without clinical signoff or cancellation. |
| **Post Lab Result** | `ORDERED` | `COMPLETED` | Produces a unique `RESULTS` entity in `PENDING_REVIEW` and marks parent `ORDERS.order_status = 'COMPLETED'` atomically. |
| **Physician Signoff** | `PENDING_REVIEW` | `REVIEWED` | Attending physician verifies lab result, locking row and writing an immutable audit log entry. |

---

## 4. Entity-Relationship Data Model (ERD)

```mermaid
erDiagram
    PATIENTS ||--o{ APPOINTMENTS : "schedules"
    PATIENTS ||--o{ ENCOUNTERS : "receives"
    PATIENTS ||--o{ ORDERS : "ordered for"
    PATIENTS ||--o{ OBSERVATIONS : "measured on"
    
    APPOINTMENTS ||--o| ENCOUNTERS : "initiates"
    
    ENCOUNTERS ||--o{ OBSERVATIONS : "records"
    ENCOUNTERS ||--o{ ORDERS : "requisitions"
    
    ORDERS ||--o| RESULTS : "produces"
    
    AUDIT_LOG {
        NUMBER audit_id PK
        VARCHAR2 entity_type
        NUMBER entity_id
        VARCHAR2 action
        VARCHAR2 actor
        CLOB previous_state
        CLOB new_state
        VARCHAR2 correlation_id
        TIMESTAMP changed_at
    }

    DATA_QUALITY_ISSUES {
        NUMBER issue_id PK
        VARCHAR2 rule_code
        VARCHAR2 severity
        VARCHAR2 affected_entity
        NUMBER entity_id
        VARCHAR2 resolution_status
    }
```

### Relational Schema Specifications

| Table Name | Primary Key | Foreign Keys & Relationships | Key Constraints & Invariants |
| :--- | :--- | :--- | :--- |
| `PATIENTS` | `patient_id` (Identity) | Referenced by Appts, Encounters, Orders | `uq_patients_mrn` (UNIQUE), Status in `('ACTIVE', 'INACTIVE', 'MERGED')` |
| `APPOINTMENTS` | `appointment_id` (Identity) | `patient_id` -> `PATIENTS(patient_id)` | Status in `('SCHEDULED', 'CHECKED_IN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW')` |
| `ENCOUNTERS` | `encounter_id` (Identity) | `patient_id`, `appointment_id` | Status in `('OPEN', 'IN_PROGRESS', 'AWAITING_RESULTS', 'COMPLETED', 'CANCELLED')`, `end_time >= start_time` |
| `OBSERVATIONS` | `observation_id` (Identity) | `encounter_id`, `patient_id` | Status in `('PRELIMINARY', 'FINAL', 'AMENDED', 'CANCELLED')` |
| `ORDERS` | `order_id` (Identity) | `encounter_id`, `patient_id` | Priority in `('STAT', 'URGENT', 'ROUTINE')`, `completed_at >= ordered_at` |
| `RESULTS` | `result_id` (Identity) | `order_id` -> `ORDERS(order_id)` (UNIQUE) | Flag in `('NORMAL', 'HIGH', 'LOW', 'CRITICAL')`, Status in `('PENDING_REVIEW', 'REVIEWED', 'AMENDED')` |
| `DATA_QUALITY_ISSUES` | `issue_id` (Identity) | Points to entity ID | Severity in `('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')`, Resolution in `('OPEN', 'RESOLVED', 'FALSE_POSITIVE')` |
| `AUDIT_LOG` | `audit_id` (Identity) | Surrogate GUID correlation ID | Immutable change tracking with before-and-after JSON CLOB states |
| `STATUS_HISTORY` | `history_id` (Identity) | Points to entity ID | Chronological audit of `from_status` -> `to_status` |

---

## 5. SQL Performance Investigations & CBO Execution Plans

<p align="center">
  <img src="assets/careflow_performance_comparison.svg" alt="Oracle CBO Execution Plan Benchmark" width="100%">
</p>

### Investigation Summary

| Investigation | Target Query | Baseline Execution Plan | Optimized Execution Plan | CBO Cost Reduction | Measured Impact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Investigation 1** | Patient Wait Times by Dept & Arrival Hour (Report 02) | `TABLE ACCESS FULL` on APPOINTMENTS & ENCOUNTERS with `HASH JOIN` | `INDEX RANGE SCAN` on composite covering index `(department, appointment_time, check_in_time, appointment_id)` | **85 &rarr; 12 (-85.8%)** | Eliminated multi-block table scans; queries satisfied entirely from indexed B-Tree leaves. |
| **Investigation 2** | Results Review Queue Prioritized by Abnormal Flag (Report 05) | `TABLE ACCESS FULL` scanning historical reviewed results + `SORT ORDER BY` | `INDEX RANGE SCAN` on composite index `(result_status, abnormal_flag, result_time, order_id)` | **112 &rarr; 18 (-83.9%)** | Bypassed 95%+ of historical reviewed results; avoided in-memory sorting overhead. |

*Full execution plans, predicate information, and analysis scripts are documented in [`docs/sql-performance.md`](file:///c:/Users/saiya/Desktop/1/docs/sql-performance.md).*

---

## 6. Predefined Analytical SQL Reports Catalog

| Report ID | Title & Business Question | Key Tables & Joins | Analytical SQL Features Used |
| :--- | :--- | :--- | :--- |
| **`RPT_01_DAILY_SCHEDULE`** | Full daily schedule with patient details, arrival timestamps, and waiting durations | `APPOINTMENTS`, `PATIENTS`, `ENCOUNTERS` | Conditional status expressions, date range filters |
| **`RPT_02_WAITING_TIME`** | Wait duration (minutes from check-in to exam) by department and arrival hour | `APPOINTMENTS`, `ENCOUNTERS` | `EXTRACT(HOUR FROM ...)`, `PERCENTILE_CONT(0.50)` |
| **`RPT_03_ENCOUNTER_COMPLETION`** | Visit cycle time (minutes start to end) by provider and encounter type | `ENCOUNTERS`, `PATIENTS` | Duration aggregations (`AVG`, `MIN`, `MAX`), CTEs |
| **`RPT_04_PENDING_ORDERS`** | Backlog of diagnostic orders awaiting lab processing with aging hours | `ORDERS`, `PATIENTS`, `ENCOUNTERS` | Priority case sorting (`STAT` &rarr; `URGENT` &rarr; `ROUTINE`) |
| **`RPT_05_AWAITING_REVIEW`** | Completed lab results awaiting physician review, critical flags first | `RESULTS`, `ORDERS`, `PATIENTS` | Abnormal flag ranking (`CRITICAL` &rarr; `HIGH` &rarr; `LOW`) |
| **`RPT_06_ORDER_TURNAROUND`** | Laboratory turnaround time (hours) by test code and priority | `ORDERS`, `RESULTS` | Diagnostic turnaround duration metrics by test panel |
| **`RPT_07_CANCELLATIONS_NOSHOW`** | Cancellation and no-show rate percentages across departments | `APPOINTMENTS` | Lost capacity percentages (`COUNT(CANCELLED) / TOTAL`) |
| **`RPT_08_DATA_QUALITY`** | Active data-integrity exceptions, rule codes, and detection aging | `DATA_QUALITY_ISSUES` | Severity sorting, resolution audit tracking |

---

## 7. Data Quality & Root-Cause Remediation Rules

| Rule Code | Severity | Target Entity | Invariant Anomaly Detected | Corrective Remediation Action |
| :--- | :--- | :--- | :--- | :--- |
| **`DQ_MISSING_CHECKIN_TIME`** | **HIGH** | `APPOINTMENT` | Status is `CHECKED_IN` but `check_in_time` is `NULL` | Verify kiosk terminal arrival log; backfill timestamp or reset state |
| **`DQ_MISSING_COMPLETION_TIME`** | **MEDIUM** | `ORDER` | Order status is `COMPLETED` but `completed_at` is `NULL` | Check linked result completion timestamp and backfill |
| **`DQ_COMPLETED_ENC_WITH_PENDING_ORDERS`** | **CRITICAL** | `ENCOUNTER` | Encounter marked `COMPLETED` despite open pending orders | Confirm whether diagnostic tests were orphaned or cancelled |
| **`DQ_INVALID_TIMESTAMP_SEQUENCE`** | **CRITICAL** | `ENCOUNTER` | Encounter `end_time` precedes `start_time` | Correct clock sync discrepancy using audit trail history |
| **`DQ_ORPHANED_RESULT`** | **CRITICAL** | `RESULT` | Result record references nonexistent or deleted order | Trace lab HL7/FHIR message source; associate with valid order |

---

## 8. Getting Started & Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Docker (optional, for running Oracle Database Free container)

### Step 1: Clone Repository
```bash
git clone https://github.com/SAIYAMgade/CareFlow.git
cd CareFlow
cp .env.example .env
```

*By default, `.env` runs in standalone mode (`DATABASE_DIALECT=sqlite`) for instant zero-dependency evaluation. Set `DATABASE_DIALECT=oracle` when connecting to Oracle Database Free.*

### Step 2: Install Python Backend Dependencies
```bash
python -m pip install -r backend/requirements.txt
```

### Step 3: Seed Synthetic Demonstration Data
Generates 450+ realistic relational records (50 patients, 120 appointments, 85 encounters, 170 vitals, 100 orders & results, 5 controlled DQ test cases):
```bash
python scripts/seed_data.py
```

### Step 4: Run Backend API
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- API Base: `http://localhost:8000`
- Interactive Swagger Documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### Step 5: Start Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser. *(The backend at `http://localhost:8000` also serves the production built SPA directly).*

---

## 9. Automated Testing & Honest Verification

Run the full automated test suite:
```bash
python -m pytest backend/app/tests -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-8.4.2
collected 14 items

backend/app/tests/test_appointments.py::test_create_and_check_in_appointment PASSED [  7%]
backend/app/tests/test_appointments.py::test_cancel_appointment_workflow PASSED     [ 14%]
backend/app/tests/test_data_quality.py::test_data_quality_detection_and_remediation PASSED [ 21%]
backend/app/tests/test_encounters.py::test_encounter_workflow_and_pending_orders_rule PASSED [ 28%]
backend/app/tests/test_oracle_integration.py::TestOracleDatabaseFreeIntegration::test_oracle_version_and_connectivity SKIPPED [ 35%]
backend/app/tests/test_oracle_integration.py::TestOracleDatabaseFreeIntegration::test_oracle_schema_objects_present SKIPPED [ 42%]
backend/app/tests/test_oracle_integration.py::TestOracleDatabaseFreeIntegration::test_oracle_plsql_package_validity SKIPPED [ 50%]
backend/app/tests/test_orders_results.py::test_order_result_review_lifecycle PASSED [ 57%]
backend/app/tests/test_patients.py::test_list_patients PASSED                        [ 64%]
backend/app/tests/test_patients.py::test_register_patient_success PASSED             [ 71%]
backend/app/tests/test_patients.py::test_register_patient_duplicate_mrn_rejected PASSED [ 78%]
backend/app/tests/test_reports.py::test_report_catalog PASSED                        [ 85%]
backend/app/tests/test_reports.py::test_execute_all_eight_reports PASSED             [ 92%]
backend/app/tests/test_reports.py::test_export_report_csv_with_formula_escaping PASSED [100%]

======================== 11 passed, 3 skipped in 5.41s ========================
```

**Quality Assurance Truthfulness:**
- All 11 unit, workflow rule, report execution, and CSV security tests execute and pass.
- Oracle integration tests (`TestOracleDatabaseFreeIntegration`) run when Oracle Database Free is online; when Oracle is unreachable, they are explicitly marked as **`SKIPPED (UNVERIFIED)`** rather than falsely green.

---

## 10. Five-Minute Technical Interview Demonstration

Follow this sequence during a technical portfolio demonstration:

1. **Minute 1: Operations Dashboard**
   - Open `http://localhost:5173`. Point out the 8 real-time KPI cards derived from persisted records and the hourly volume and wait time charts.
2. **Minute 2: Relational Check-In & Atomic Transaction**
   - Go to **Appointments**. Select a patient in `SCHEDULED` status and click **Check In**. Show the atomic update: records arrival time and auto-generates a new `ENCOUNTER` record. Attempt duplicate check-in to demonstrate the HTTP 409 rejection.
3. **Minute 3: Clinical Safety Gate & Order Completion**
   - Go to **Encounters**. Open an encounter, click **Place Lab Order** (`CBC`). Attempt to mark the encounter `COMPLETED`. Show the safety gate rejection ("pending orders remain"). Switch to **Orders & Results**, click **Post Result** on the order, sign it off, and return to conclude the encounter.
4. **Minute 4: Data Quality & Root-Cause Remediation**
   - Go to **Data Quality**. Click **Run Live Integrity Audit**. Show the detected anomaly (`DQ_MISSING_CHECKIN_TIME`). Click **Remediate**, enter investigation notes ("Kiosk network timeout; arrival verified from badge reader"), and submit. Open **Audit Explorer** to view the immutable audit trail.
5. **Minute 5: Analytical Reporting & Query Performance**
   - Open **Reporting Workspace**. Select **Report 02 (Patient Waiting Time)**. Run the query, inspect execution time (1-2 ms), export to CSV, and switch to the **SQL Query** tab to explain the underlying CTEs and the 85.8% execution plan cost reduction.

---

## 11. Top 5 Engineering Decisions

1. **Database as Single Source of Truth:** Enforced schema constraints (foreign keys, check constraints, unique MRNs) and PL/SQL packages rather than relying purely on client-side validation.
2. **Dual-Engine Persistence:** Supported Oracle Database Free via `python-oracledb` Thin mode while retaining a lightweight standalone fallback engine so evaluators can test the platform with zero Docker friction.
3. **Clinical Safety Gates:** Modeled realistic healthcare rules—specifically preventing encounter signoff when diagnostic orders are pending.
4. **Honest Quality Assurance:** Refused to fabricate Oracle test results or badge status in CI; offline Oracle tests are explicitly skipped as unverified.
5. **Defense-in-Depth CSV Security:** Implemented formula injection sanitization on all exported reporting spreadsheets.

---

## 12. License

MIT License. Designed and engineered for technical portfolio demonstration.
