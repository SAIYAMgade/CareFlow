# CareFlow REST API Documentation

All API endpoints are served under the `/api` prefix and provide interactive Swagger documentation at `/docs` and ReDoc at `/redoc`.

---

## 1. Centralized Error Format

All error responses adhere to a consistent contract:

```json
{
  "error": true,
  "code": "INVALID_STATE_TRANSITION",
  "message": "Cannot check in appointment. Current status is CHECKED_IN. Expected SCHEDULED.",
  "details": {
    "appointment_id": 5,
    "current_status": "CHECKED_IN"
  }
}
```

### Standard Status Codes:
- `200 OK`: Request succeeded.
- `201 Created`: Entity created successfully.
- `400 Bad Request`: Data integrity violation or database constraint rejection.
- `404 Not Found`: Entity not found.
- `409 Conflict`: Invalid state transition or concurrent workflow conflict.
- `422 Unprocessable Entity`: Schema or Pydantic validation failure.

---

## 2. API Endpoints Catalog

### Dashboard
- `GET /api/dashboard/stats`: Returns operational KPIs (appointments today, checked in, waiting, encounters in progress, orders awaiting results, open DQ issues).
- `GET /api/dashboard/charts`: Returns aggregated charts (hourly volume, wait times by department, encounter status distribution, order turnaround time).

### Patients
- `GET /api/patients`: Paginated list of patients with search (`search`) and status filter (`status`).
- `POST /api/patients`: Registers a new patient. Auto-generates unique MRN if omitted.
- `GET /api/patients/{patient_id}`: Retrieves demographic details for a single patient.
- `PUT /api/patients/{patient_id}`: Updates permitted demographic fields.

### Appointments
- `GET /api/appointments`: Paginated list filtered by `date`, `department`, `status`, `patient_id`.
- `POST /api/appointments`: Books a new appointment in `SCHEDULED` status.
- `GET /api/appointments/{id}`: Retrieves appointment details with patient demographics.
- `POST /api/appointments/{id}/check-in`: Transitions status to `CHECKED_IN`, sets arrival time, and auto-generates an initial clinical encounter.
- `POST /api/appointments/{id}/cancel`: Cancels appointment with mandatory `cancel_reason`.
- `POST /api/appointments/{id}/reschedule`: Reschedules a `SCHEDULED` appointment to a new date/time.

### Encounters
- `GET /api/encounters`: Paginated list filtered by `department`, `status`, `patient_id`.
- `POST /api/encounters`: Creates an encounter record.
- `GET /api/encounters/{id}`: Retrieves encounter details, clinical notes, and complaint.
- `PUT /api/encounters/{id}/status`: Transitions encounter state. **Enforces pending orders check before allowing `COMPLETED`.**
- `PUT /api/encounters/{id}/notes`: Updates clinical documentation notes with audit trail.

### Observations
- `GET /api/observations`: Lists observations by `encounter_id` or `patient_id`.
- `POST /api/observations`: Logs a vital sign or physical observation.

### Orders & Results
- `GET /api/orders`: Paginated list filtered by `encounter_id`, `patient_id`, `status`, `priority`.
- `POST /api/orders`: Places a diagnostic order (`CBC`, `BMP`, `LIPID`, `TSH`, `HBA1C`, `UA`).
- `GET /api/orders/{id}`: Retrieves single order details.
- `POST /api/orders/{id}/complete`: Atomically creates a `RESULT` and marks the order `COMPLETED`.
- `GET /api/results`: Paginated list of lab results with filters (`result_status`, `abnormal_only`).
- `POST /api/results/{id}/review`: Physician clinical signoff marking result `REVIEWED`.

### Reporting Workspace
- `GET /api/reports/catalog`: Returns metadata, business questions, and parameters for all 8 predefined reports.
- `POST /api/reports/execute`: Executes a parameterized report query with database execution timing and pagination.
- `POST /api/reports/export`: Streams an RFC 4180-compliant CSV download with formula-injection escaping.

### Data Quality & Remediation
- `GET /api/data-quality/issues`: Lists detected integrity issues with filters (`status`, `severity`, `entity`).
- `POST /api/data-quality/scan`: Triggers live invariant scan across the database.
- `POST /api/data-quality/issues/{id}/resolve`: Resolves an issue with mandatory remediation notes and audit trail.

### Audit & System Health
- `GET /api/audit`: Searchable system audit log.
- `GET /api/audit/history/{entity_type}/{entity_id}`: Chronological status transitions for an entity.
- `GET /api/health`: Comprehensive system health, database connection ping, and engine dialect.
