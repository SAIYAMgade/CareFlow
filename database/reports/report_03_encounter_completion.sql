-- ============================================================================
-- Report 03: Encounter Completion & Cycle Time Analysis
-- Business Question:
--   How long do patient encounters take to complete (start to end), broken down
--   by encounter type, department, and provider?
-- Relevant Tables: ENCOUNTERS, PATIENTS
-- ============================================================================

WITH encounter_durations AS (
    SELECT 
        e.encounter_id,
        e.encounter_type,
        e.department,
        e.provider_name,
        e.status,
        e.start_time,
        e.end_time,
        ROUND(
            EXTRACT(DAY FROM (e.end_time - e.start_time)) * 1440 +
            EXTRACT(HOUR FROM (e.end_time - e.start_time)) * 60 +
            EXTRACT(MINUTE FROM (e.end_time - e.start_time)) +
            EXTRACT(SECOND FROM (e.end_time - e.start_time)) / 60,
            1
        ) AS duration_minutes
    FROM ENCOUNTERS e
    WHERE e.status = 'COMPLETED'
      AND e.end_time IS NOT NULL
      AND (:p_start_date IS NULL OR TRUNC(CAST(e.start_time AS DATE)) >= TO_DATE(:p_start_date, 'YYYY-MM-DD'))
      AND (:p_end_date IS NULL OR TRUNC(CAST(e.start_time AS DATE)) <= TO_DATE(:p_end_date, 'YYYY-MM-DD'))
      AND (:p_department IS NULL OR e.department = :p_department)
)
SELECT 
    department,
    encounter_type,
    provider_name,
    COUNT(*) AS completed_encounters_count,
    ROUND(AVG(duration_minutes), 1) AS avg_duration_minutes,
    MIN(duration_minutes) AS min_duration_minutes,
    MAX(duration_minutes) AS max_duration_minutes,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_minutes), 1) AS median_duration_minutes
FROM encounter_durations
GROUP BY department, encounter_type, provider_name
ORDER BY department, encounter_type, provider_name;
