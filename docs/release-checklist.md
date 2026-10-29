# CareFlow Release Validation Checklist

Use this checklist prior to committing release builds or deploying CareFlow for evaluation.

---

## 1. Environment & Configuration
- [x] `.env.example` contains placeholders with no plaintext credentials.
- [x] `.env` is ignored by `.gitignore`.
- [x] `DATABASE_DIALECT` cleanly toggles between `oracle` and `sqlite`.
- [x] Health check endpoint `GET /api/health` reports status, engine, and version accurately.

---

## 2. Relational Database & PL/SQL
- [x] Schema DDL (`01_tables_and_constraints.sql`) executes with zero syntax errors.
- [x] Foreign keys with referential constraints are defined on all relationships.
- [x] Covering indexes exist for search, scheduling, and review queue query patterns.
- [x] PL/SQL package specification (`careflow_workflow_pkg.pks`) compiles with `STATUS = 'VALID'`.
- [x] PL/SQL package body (`careflow_workflow_pkg.pkb`) compiles with `STATUS = 'VALID'`.
- [x] Status history and audit log triggers capture entity mutations.

---

## 3. Workflow Invariants & Integrity
- [x] Patient unique MRN constraint enforced at database layer.
- [x] Appointment check-in atomically opens a new encounter in a single transaction.
- [x] Encounter completion is blocked if pending diagnostic orders exist.
- [x] Diagnostic order completion atomically creates result record and sets timestamp.
- [x] Re-reviewing already signed-off results is rejected with HTTP 409.

---

## 4. Test Suite Execution
- [x] `python -m pytest backend/app/tests -v` passes with zero failures.
- [x] All 11 unit, workflow rule, and report tests pass.
- [x] Oracle integration tests report honest status (executed if Oracle is online, skipped if offline).
- [x] CSV report export escapes formula injection characters (`=`, `+`, `-`, `@`).

---

## 5. Frontend & UI
- [x] `npm run build` in `frontend/` compiles with zero TypeScript errors.
- [x] Responsive layout verified across desktop, tablet, and mobile breakpoints.
- [x] High-contrast operational status badges for all states.
- [x] Confirmation dialogs implemented for check-in, cancellation, and remediation.
- [x] Environment badge visibly displays `SIMULATED CLINICAL ENVIRONMENT - SYNTHETIC DATA`.
