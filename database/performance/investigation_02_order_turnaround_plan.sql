-- ============================================================================
-- SQL Performance Investigation 02: Pending Orders Review & Abnormal Flag Indexing
-- Target Query: Report 05 (Orders awaiting clinical review prioritized by abnormal flag)
-- ============================================================================

-- Step 1: Explain Plan Baseline (Full Table Scan on RESULTS)
EXPLAIN PLAN SET STATEMENT_ID = 'REVIEW_BASELINE' FOR
SELECT 
    r.result_id,
    r.result_time,
    r.result_value,
    r.abnormal_flag,
    o.order_id,
    o.order_code,
    p.mrn,
    p.last_name
FROM RESULTS r
JOIN ORDERS o ON r.order_id = o.order_id
JOIN PATIENTS p ON o.patient_id = p.patient_id
WHERE r.result_status = 'PENDING_REVIEW'
ORDER BY 
    CASE r.abnormal_flag 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'LOW' THEN 3 
        ELSE 4 
    END ASC,
    r.result_time ASC;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY('PLAN_TABLE', 'REVIEW_BASELINE', 'TYPICAL'));

-- Step 2: Optimized Query utilizing Composite Index on RESULTS (result_status, abnormal_flag, result_time)
-- CREATE INDEX idx_res_status_flag_time ON RESULTS (result_status, abnormal_flag, result_time, order_id);

EXPLAIN PLAN SET STATEMENT_ID = 'REVIEW_OPTIMIZED' FOR
SELECT /*+ INDEX(r idx_res_status_flag_time) */
    r.result_id,
    r.result_time,
    r.result_value,
    r.abnormal_flag,
    o.order_id,
    o.order_code,
    p.mrn,
    p.last_name
FROM RESULTS r
JOIN ORDERS o ON r.order_id = o.order_id
JOIN PATIENTS p ON o.patient_id = p.patient_id
WHERE r.result_status = 'PENDING_REVIEW'
ORDER BY 
    CASE r.abnormal_flag 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'LOW' THEN 3 
        ELSE 4 
    END ASC,
    r.result_time ASC;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY('PLAN_TABLE', 'REVIEW_OPTIMIZED', 'TYPICAL'));
