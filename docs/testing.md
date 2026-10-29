# CareFlow Testing Strategy & Test Execution Guide

## 1. Testing Philosophy

The CareFlow testing suite is architected to test application behavior from unit validation to database-level transactional safety.

In strict adherence to project integrity standards:
- **Zero Fabricated Results:** Tests that require an actual running Oracle Database Free instance are run against Oracle when reachable. If Oracle is offline, those tests are **explicitly marked as UNVERIFIED / SKIPPED**, never falsely reported as passing or substituted with SQLite results.
- **Dual-Engine Validation:** Standard unit, API, and workflow rule tests execute deterministically against the relational seed dataset.

---

## 2. Test Suite Structure

```
backend/app/tests/
├── conftest.py                   # Session fixtures, client setup & deterministic seed
├── test_patients.py              # Patient registration, search, duplicate MRN rejection
├── test_appointments.py          # State transitions, atomic check-in, cancellations
├── test_encounters.py            # Clinical workflow rules, pending-orders completion gate
├── test_orders_results.py        # Order placement, result posting, physician review signoff
├── test_reports.py               # Validation of all 8 reports & CSV formula escaping
├── test_data_quality.py          # Rule anomaly detection & controlled remediation audit
└── test_oracle_integration.py    # Oracle Database Free live integration (oracledb)
```

---

## 3. Key Test Scenarios Covered

1. **Successful Patient Registration:** Validates demographics, automatic MRN generation (`MRN-2026-XXXXX`), and initial `ACTIVE` status.
2. **Duplicate MRN Rejection:** Verifies database unique constraint enforcement; duplicate registration returns HTTP 400 with `DATA_INTEGRITY_VIOLATION`.
3. **Atomic Appointment Check-In:** Verifies appointment transitions from `SCHEDULED` to `CHECKED_IN`, sets arrival timestamp, and atomically opens an initial `ENCOUNTER` record in `OPEN` status.
4. **Invalid State Transition Rejection:** Verifies that checking in an already checked-in or cancelled appointment is rejected with HTTP 409 `INVALID_STATE_TRANSITION`.
5. **Encounter Completion Safety Gate:** Verifies that an encounter cannot be marked `COMPLETED` when active diagnostic orders remain in `ORDERED` or `IN_PROGRESS` status.
6. **Order & Result Atomic Lifecycle:** Verifies diagnostic order placement, result posting with abnormal flags, order auto-completion, duplicate result prevention, and clinical signoff.
7. **Report Catalog Execution:** Verifies all 8 analytical SQL reports execute without syntax or parameter binding errors.
8. **CSV Formula Injection Defense:** Verifies that report CSV exports sanitize potentially dangerous spreadsheet formula prefixes (`=`, `+`, `-`, `@`, `\t`, `\r`) by prepending a single quote (`'`).
9. **Data Quality Audit & Remediation:** Verifies automated anomaly detection across 5 integrity rules, and tests resolving an issue with remediation documentation and audit preservation.
10. **Oracle Database Free Integration:** Verifies schema objects, constraints, and PL/SQL package compilation status (`CAREFLOW_WORKFLOW_PKG`) against live Oracle.

---

## 4. Test Execution Commands

### Run Full Test Suite:
```bash
python -m pytest backend/app/tests -v
```

### Run Only Unit & Workflow Rules (Excluding Oracle Live Tests):
```bash
python -m pytest backend/app/tests -v -k "not TestOracleDatabaseFreeIntegration"
```

### Run Oracle Integration Tests Specifically:
```bash
python -m pytest backend/app/tests/test_oracle_integration.py -v
```

*Note: If Oracle is not reachable, `test_oracle_integration.py` will report:*
`SKIPPED: Oracle Database Free (localhost:1521/FREEPDB1) is not running or unreachable in this host environment. Per Section 12/18 rules, Oracle integration tests are explicitly marked as UNVERIFIED rather than substituted.`
