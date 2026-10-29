-- ============================================================================
-- Report 07: Appointment Cancellation and No-Show Analysis
-- Business Question:
--   What are the clinic-wide cancellation and no-show rates across departments,
--   and what are the primary stated cancellation reasons?
-- Relevant Tables: APPOINTMENTS
-- ============================================================================

WITH appt_summary AS (
    SELECT 
        department,
        appointment_type,
        COUNT(*) AS total_booked,
        COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) AS completed_count,
        COUNT(CASE WHEN status = 'CANCELLED' THEN 1 END) AS cancelled_count,
        COUNT(CASE WHEN status = 'NO_SHOW' THEN 1 END) AS noshow_count
    FROM APPOINTMENTS
    WHERE (:p_start_date IS NULL OR TRUNC(CAST(appointment_time AS DATE)) >= TO_DATE(:p_start_date, 'YYYY-MM-DD'))
      AND (:p_end_date IS NULL OR TRUNC(CAST(appointment_time AS DATE)) <= TO_DATE(:p_end_date, 'YYYY-MM-DD'))
      AND (:p_department IS NULL OR department = :p_department)
    GROUP BY department, appointment_type
)
SELECT 
    department,
    appointment_type,
    total_booked,
    completed_count,
    cancelled_count,
    noshow_count,
    ROUND((cancelled_count * 100.0) / NULLIF(total_booked, 0), 1) AS cancellation_rate_pct,
    ROUND((noshow_count * 100.0) / NULLIF(total_booked, 0), 1) AS noshow_rate_pct,
    ROUND(((cancelled_count + noshow_count) * 100.0) / NULLIF(total_booked, 0), 1) AS lost_capacity_pct
FROM appt_summary
ORDER BY lost_capacity_pct DESC, department ASC;
