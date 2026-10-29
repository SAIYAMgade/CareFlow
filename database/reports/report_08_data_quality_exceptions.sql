-- ============================================================================
-- Report 08: Data Quality Exception and Integrity Audit
-- Business Question:
--   What active data-integrity or workflow exceptions have been flagged, categorized
--   by severity, affected entity, and aging duration since detection?
-- Relevant Tables: DATA_QUALITY_ISSUES
-- ============================================================================

SELECT 
    issue_id,
    rule_code,
    severity,
    affected_entity,
    entity_id,
    detection_time,
    description,
    investigation_steps,
    resolution_status,
    resolved_by,
    resolved_at,
    remediation_notes,
    ROUND(
        EXTRACT(DAY FROM (SYSTIMESTAMP - detection_time)) * 24 +
        EXTRACT(HOUR FROM (SYSTIMESTAMP - detection_time)) +
        EXTRACT(MINUTE FROM (SYSTIMESTAMP - detection_time)) / 60,
        1
    ) AS age_hours
FROM DATA_QUALITY_ISSUES
WHERE (:p_status IS NULL OR resolution_status = :p_status)
  AND (:p_severity IS NULL OR severity = :p_severity)
  AND (:p_entity IS NULL OR affected_entity = :p_entity)
ORDER BY 
    CASE severity 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'MEDIUM' THEN 3 
        ELSE 4 
    END ASC,
    detection_time DESC;
