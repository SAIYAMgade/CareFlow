-- ============================================================================
-- Report 02: Patient Waiting Time Analysis
-- Business Question:
--   What is the average, minimum, and maximum waiting time (minutes from check-in
--   to encounter start) grouped by department and arrival hour?
-- Relevant Tables: APPOINTMENTS, ENCOUNTERS
-- ============================================================================

WITH wait_calculations AS (
    SELECT 
        a.department,
        EXTRACT(HOUR FROM a.check_in_time) AS arrival_hour,
        ROUND(
            EXTRACT(DAY FROM (e.start_time - a.check_in_time)) * 1440 +
            EXTRACT(HOUR FROM (e.start_time - a.check_in_time)) * 60 +
            EXTRACT(MINUTE FROM (e.start_time - a.check_in_time)) +
            EXTRACT(SECOND FROM (e.start_time - a.check_in_time)) / 60,
            1
        ) AS wait_minutes
    FROM APPOINTMENTS a
    JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
    WHERE a.check_in_time IS NOT NULL
      AND e.start_time >= a.check_in_time
      AND (:p_start_date IS NULL OR TRUNC(CAST(a.appointment_time AS DATE)) >= TO_DATE(:p_start_date, 'YYYY-MM-DD'))
      AND (:p_end_date IS NULL OR TRUNC(CAST(a.appointment_time AS DATE)) <= TO_DATE(:p_end_date, 'YYYY-MM-DD'))
      AND (:p_department IS NULL OR a.department = :p_department)
)
SELECT 
    department,
    arrival_hour,
    COUNT(*) AS total_patients_seen,
    ROUND(AVG(wait_minutes), 1) AS avg_wait_minutes,
    MIN(wait_minutes) AS min_wait_minutes,
    MAX(wait_minutes) AS max_wait_minutes,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY wait_minutes), 1) AS median_wait_minutes
FROM wait_calculations
GROUP BY department, arrival_hour
ORDER BY department, arrival_hour;
