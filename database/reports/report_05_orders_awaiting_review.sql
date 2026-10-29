-- ============================================================================
-- Report 05: Completed Orders Awaiting Provider Review
-- Business Question:
--   Which lab results have been reported by the laboratory but not yet signed off
--   or reviewed by the ordering clinician, prioritized by abnormal/critical flags?
-- Relevant Tables: RESULTS, ORDERS, PATIENTS, ENCOUNTERS
-- ============================================================================

SELECT 
    r.result_id,
    r.result_time,
    r.result_value,
    r.unit,
    r.reference_range,
    r.abnormal_flag,
    r.result_status,
    o.order_id,
    o.order_code,
    o.order_name,
    o.priority,
    o.ordered_by,
    p.patient_id,
    p.mrn,
    p.first_name || ' ' || p.last_name AS patient_name,
    e.encounter_id,
    e.department,
    ROUND(
        EXTRACT(DAY FROM (SYSTIMESTAMP - r.result_time)) * 24 +
        EXTRACT(HOUR FROM (SYSTIMESTAMP - r.result_time)) +
        EXTRACT(MINUTE FROM (SYSTIMESTAMP - r.result_time)) / 60,
        1
    ) AS hours_since_result
FROM RESULTS r
JOIN ORDERS o ON r.order_id = o.order_id
JOIN PATIENTS p ON o.patient_id = p.patient_id
JOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id
WHERE r.result_status = 'PENDING_REVIEW'
  AND (:p_abnormal_only IS NULL OR (:p_abnormal_only = 'Y' AND r.abnormal_flag IN ('HIGH', 'LOW', 'CRITICAL')))
  AND (:p_department IS NULL OR e.department = :p_department)
ORDER BY 
    CASE r.abnormal_flag 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'LOW' THEN 3 
        ELSE 4 
    END ASC,
    r.result_time ASC;
