-- ============================================================================
-- CareFlow Healthcare Operations Platform
-- Oracle Database Free (23ai / 21c) Index Definitions
-- 02_indexes.sql
-- ============================================================================

-- 1. Patient Name Lookup & Search Index
-- Query Pattern: Fast patient registry searches filtering/sorting by name
CREATE INDEX idx_patients_name 
ON PATIENTS (last_name, first_name);

-- 2. Appointment Operational Scheduling & Status Index
-- Query Pattern: Daily appointment schedule query, filtering by department, date range, status
CREATE INDEX idx_appts_time_dept_status 
ON APPOINTMENTS (appointment_time, department, status);

-- 3. Patient Appointment History Index
-- Query Pattern: Fetching all appointments for a patient in chronological order
CREATE INDEX idx_appts_patient_time 
ON APPOINTMENTS (patient_id, appointment_time DESC);

-- 4. Active Encounters & Patient Chart Index
-- Query Pattern: Listing encounters for a specific patient or filtering by clinic status
CREATE INDEX idx_enc_patient_status 
ON ENCOUNTERS (patient_id, status);

-- 5. Encounter Appointment Lookup Index
-- Query Pattern: Foreign key lookup joining appointments to encounters
CREATE INDEX idx_enc_appt_id 
ON ENCOUNTERS (appointment_id);

-- 6. Encounter Timeline & Cycle Time Reporting Index
-- Query Pattern: Range queries on start_time and department for cycle time and waiting time analytics
CREATE INDEX idx_enc_start_dept_status 
ON ENCOUNTERS (start_time, department, status);

-- 7. Observations Lookup Index
-- Query Pattern: Finding vitals and observations for a specific encounter
CREATE INDEX idx_obs_encounter_code 
ON OBSERVATIONS (encounter_id, observation_code);

-- 8. Orders by Encounter & Status Index
-- Query Pattern: Workflow validation ensuring encounters don't close with pending orders
CREATE INDEX idx_ord_encounter_status 
ON ORDERS (encounter_id, order_status);

-- 9. Pending Orders Backlog & Turnaround Analysis Index
-- Query Pattern: Finding orders in ORDERED / IN_PROGRESS status sorted by ordered_at
CREATE INDEX idx_ord_status_ordered 
ON ORDERS (order_status, ordered_at);

-- 10. Results Review Queue Index
-- Query Pattern: Finding completed laboratory results awaiting provider review (result_status, abnormal_flag)
CREATE INDEX idx_res_status_flag 
ON RESULTS (result_status, abnormal_flag);

-- 11. Data Quality Investigation Index
-- Query Pattern: Dashboard alerts and audit reports filtering by resolution_status and severity
CREATE INDEX idx_dq_status_severity 
ON DATA_QUALITY_ISSUES (resolution_status, severity, detection_time DESC);

-- 12. Audit Trail Chronological Index
-- Query Pattern: Audit explorer filtering by entity_type, entity_id, and ordered by changed_at
CREATE INDEX idx_audit_entity_time 
ON AUDIT_LOG (entity_type, entity_id, changed_at DESC);

-- 13. Status History Chronological Index
-- Query Pattern: Chronological timeline of state transitions per entity
CREATE INDEX idx_sh_entity_time 
ON STATUS_HISTORY (entity_type, entity_id, changed_at ASC);
