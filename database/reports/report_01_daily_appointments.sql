-- ============================================================================
-- Report 01: Daily Appointment Operational Schedule
-- Business Question:
--   What is the full operational schedule for a specific date, department, or
--   status, showing patient details, scheduled time, check-in time, and current workflow state?
-- Relevant Tables: APPOINTMENTS, PATIENTS, ENCOUNTERS
-- ============================================================================

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
    p.date_of_birth,
    a.check_in_time,
    e.encounter_id,
    e.status AS encounter_status,
    CASE 
        WHEN a.status = 'CHECKED_IN' AND a.check_in_time IS NOT NULL THEN
            ROUND(EXTRACT(DAY FROM (SYSTIMESTAMP - a.check_in_time)) * 1440 +
                  EXTRACT(HOUR FROM (SYSTIMESTAMP - a.check_in_time)) * 60 +
                  EXTRACT(MINUTE FROM (SYSTIMESTAMP - a.check_in_time)), 0)
        ELSE NULL
    END AS current_waiting_minutes
FROM APPOINTMENTS a
JOIN PATIENTS p ON a.patient_id = p.patient_id
LEFT JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
WHERE (:p_target_date IS NULL OR TRUNC(CAST(a.appointment_time AS DATE)) = TO_DATE(:p_target_date, 'YYYY-MM-DD'))
  AND (:p_department IS NULL OR a.department = :p_department)
  AND (:p_status IS NULL OR a.status = :p_status)
ORDER BY a.appointment_time ASC, a.appointment_id ASC;
