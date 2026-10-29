# CareFlow Business Rules & State Invariants

## 1. Healthcare Workflow State Machines

### A. Appointment Lifecycle

```
[SCHEDULED] ----> (Check-In) ---------> [CHECKED_IN]
     |                                        |
     +------> (Cancel) ---> [CANCELLED]       +-----> [IN_PROGRESS]
     |                                                    |
     +------> (No Show) --> [NO_SHOW]                     v
                                                     [COMPLETED]
```

**State Transition Rules:**
1. **Rule APPT-01 (Check-In Gate):** Only appointments in `SCHEDULED` status may transition to `CHECKED_IN`. Re-checking in an already checked-in appointment, or checking in a cancelled/completed appointment, raises `WorkflowConflictException` (HTTP 409).
2. **Rule APPT-02 (Atomic Encounter Initialization):** Checking in an appointment executes an atomic transaction: it records `check_in_time = SYSTIMESTAMP` on the appointment, logs a status history record, and simultaneously opens a new `ENCOUNTER` entity in `OPEN` status linked via `appointment_id`.
3. **Rule APPT-03 (Cancellation):** Once an appointment reaches `COMPLETED`, it cannot be cancelled or marked as a no-show. Cancellation requires a non-empty `cancel_reason`.
4. **Rule APPT-04 (Rescheduling):** Only `SCHEDULED` appointments may be rescheduled. Past or checked-in appointments cannot be silently rescheduled.

---

### B. Clinical Encounter Lifecycle & Safety Gate

```
[OPEN] (Triage) ---> [IN_PROGRESS] (Exam) ---> [AWAITING_RESULTS] ---> [COMPLETED] (Signoff)
   |                       |                          |
   +-----------------------+--------------------------+--------> [CANCELLED]
```

**Workflow Safety Rules:**
1. **Rule ENC-01 (Pending Orders Invariant):** An encounter **CANNOT** be transitioned to `COMPLETED` if there are any active orders in `ORDERED` or `IN_PROGRESS` status associated with it.
   - *Rationale:* In patient safety and clinical liability, a clinician cannot sign off and discharge a patient while diagnostic tests remain outstanding without explicit clinical review or cancellation.
   - *Enforcement:* Validated in PL/SQL (`careflow_workflow_pkg.complete_encounter`) and in the application service layer (`EncounterService.update_status`).
2. **Rule ENC-02 (Linked Appointment Completion):** When an encounter completes, any originating appointment linked via `appointment_id` is automatically concluded and marked `COMPLETED`.
3. **Rule ENC-03 (Timestamp Sequence):** Encounter `end_time` must be greater than or equal to `start_time`. Attempting to persist `end_time < start_time` is rejected by database check constraint `chk_enc_time_order`.

---

### C. Diagnostic Order & Result Lifecycle

```
[ORDERED] ---> (Dispatch) ---> [IN_PROGRESS] ---> (Post Result) ---> [COMPLETED]
                                                                          |
                                                                          v
                                                          Result: [PENDING_REVIEW]
                                                                          |
                                                                    (Sign Off)
                                                                          v
                                                                 Result: [REVIEWED]
```

**Order & Result Rules:**
1. **Rule ORD-01 (No Orders on Closed Encounters):** Orders can only be placed on active encounters (`OPEN`, `IN_PROGRESS`, `AWAITING_RESULTS`). Placing an order on a `COMPLETED` or `CANCELLED` encounter is rejected.
2. **Rule ORD-02 (Atomic Result Posting):** Posting a result via `complete_order_with_result`:
   - Enforces unique 1-to-1 relationship between `ORDERS` and `RESULTS`.
   - Creates the `RESULTS` record in `PENDING_REVIEW` status.
   - Transitions `ORDERS.order_status` to `COMPLETED` and sets `completed_at = SYSTIMESTAMP`.
   - Records audit entries for both entities.
3. **Rule RES-01 (Review Signoff):** A result in `REVIEWED` status cannot be re-reviewed unless amended through a formal change request.

---

## 2. Data Quality Rules & Anomaly Detection

| Rule Code | Severity | Target Entity | Anomaly Description | Recommended Investigation Steps |
| :--- | :--- | :--- | :--- | :--- |
| `DQ_MISSING_CHECKIN_TIME` | **HIGH** | `APPOINTMENT` | Status is `CHECKED_IN` but `check_in_time` is `NULL`. | Inspect kiosk logs; verify arrival badge time or reset state to `SCHEDULED`. |
| `DQ_MISSING_COMPLETION_TIME` | **MEDIUM** | `ORDER` | Order status is `COMPLETED` but `completed_at` is `NULL`. | Check linked `RESULTS.result_time` and backfill timestamp. |
| `DQ_COMPLETED_ENC_WITH_PENDING_ORDERS` | **CRITICAL** | `ENCOUNTER` | Encounter marked `COMPLETED` despite active pending orders. | Confirm whether pending tests were orphaned, cancelled, or missed. |
| `DQ_INVALID_TIMESTAMP_SEQUENCE` | **CRITICAL** | `ENCOUNTER` | `end_time` precedes `start_time`. | Verify device clocks and time zones; correct timestamp via audit log. |
| `DQ_ORPHANED_RESULT` | **CRITICAL** | `RESULT` | Result exists without corresponding valid `order_id`. | Trace laboratory interface feed; quarantine orphaned data. |
