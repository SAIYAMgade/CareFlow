-- ============================================================================
-- Report 04: Pending Orders Backlog & Aging Report
-- Business Question:
--   Which clinical orders are currently pending results, how long have they
--   been outstanding, and which high-priority orders require immediate attention?
-- Relevant Tables: ORDERS, PATIENTS, ENCOUNTERS
-- ============================================================================

SELECT 
    o.order_id,
    o.order_type,
    o.order_code,
    o.order_name,
    o.priority,
    o.order_status,
    o.ordered_at,
    ROUND(
        EXTRACT(DAY FROM (SYSTIMESTAMP - o.ordered_at)) * 24 +
        EXTRACT(HOUR FROM (SYSTIMESTAMP - o.ordered_at)) +
        EXTRACT(MINUTE FROM (SYSTIMESTAMP - o.ordered_at)) / 60,
        1
    ) AS age_hours,
    p.patient_id,
    p.mrn,
    p.first_name || ' ' || p.last_name AS patient_name,
    e.encounter_id,
    e.department,
    o.ordered_by
FROM ORDERS o
JOIN PATIENTS p ON o.patient_id = p.patient_id
JOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id
WHERE o.order_status IN ('ORDERED', 'IN_PROGRESS')
  AND (:p_priority IS NULL OR o.priority = :p_priority)
  AND (:p_order_type IS NULL OR o.order_type = :p_order_type)
  AND (:p_department IS NULL OR e.department = :p_department)
ORDER BY 
    CASE o.priority 
        WHEN 'STAT' THEN 1 
        WHEN 'URGENT' THEN 2 
        ELSE 3 
    END ASC,
    o.ordered_at ASC;
