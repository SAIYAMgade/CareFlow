-- ============================================================================
-- CareFlow Healthcare Operations Platform
-- Oracle Database Free (23ai / 21c) Reusable Reporting Views
-- database/views/careflow_views.sql
-- ============================================================================

-- 1. Daily Operational Schedule View
CREATE OR REPLACE VIEW vw_daily_appointment_schedule AS
SELECT 
    a.appointment_id,
    a.appointment_time,
    a.department,
    a.provider_name,
    a.appointment_type,
    a.status AS appointment_status,
    p.patient_id,
    p.mrn,
    p.first_name || ' ' || p.last_name AS patient_name,
    a.check_in_time,
    e.encounter_id,
    e.status AS encounter_status
FROM APPOINTMENTS a
JOIN PATIENTS p ON a.patient_id = p.patient_id
LEFT JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id;

-- 2. Pending Orders and Review Backlog View
CREATE OR REPLACE VIEW vw_pending_orders_review AS
SELECT 
    o.order_id,
    o.order_type,
    o.order_code,
    o.order_name,
    o.order_status,
    o.priority,
    o.ordered_at,
    p.patient_id,
    p.mrn,
    p.first_name || ' ' || p.last_name AS patient_name,
    e.encounter_id,
    e.department,
    r.result_id,
    r.result_value,
    r.unit,
    r.abnormal_flag,
    r.result_status,
    r.result_time
FROM ORDERS o
JOIN PATIENTS p ON o.patient_id = p.patient_id
JOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id
LEFT JOIN RESULTS r ON o.order_id = r.order_id;

-- 3. Encounter Cycle Time Metrics View
CREATE OR REPLACE VIEW vw_encounter_completion_metrics AS
SELECT 
    e.encounter_id,
    e.patient_id,
    e.appointment_id,
    e.encounter_type,
    e.department,
    e.provider_name,
    e.status,
    e.start_time,
    e.end_time,
    CASE 
        WHEN e.end_time IS NOT NULL THEN
            ROUND(
                EXTRACT(DAY FROM (e.end_time - e.start_time)) * 1440 +
                EXTRACT(HOUR FROM (e.end_time - e.start_time)) * 60 +
                EXTRACT(MINUTE FROM (e.end_time - e.start_time)) +
                EXTRACT(SECOND FROM (e.end_time - e.start_time)) / 60,
                1
            )
        ELSE NULL
    END AS duration_minutes
FROM ENCOUNTERS e;
