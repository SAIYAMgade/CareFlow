-- ============================================================================
-- SQL Performance Investigation 01: Patient Waiting Time Analytics
-- Target Query: Report 02 (Wait times by Department and Arrival Hour)
-- ============================================================================

-- Step 1: Explain Plan for Baseline Query (Without Composite Index)
EXPLAIN PLAN SET STATEMENT_ID = 'WAIT_BASELINE' FOR
SELECT 
    a.department,
    EXTRACT(HOUR FROM a.check_in_time) AS arrival_hour,
    COUNT(*) AS total_patients,
    ROUND(AVG(
        EXTRACT(DAY FROM (e.start_time - a.check_in_time)) * 1440 +
        EXTRACT(HOUR FROM (e.start_time - a.check_in_time)) * 60 +
        EXTRACT(MINUTE FROM (e.start_time - a.check_in_time))
    ), 1) AS avg_wait_minutes
FROM APPOINTMENTS a
JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
WHERE a.check_in_time IS NOT NULL
  AND a.department = 'Cardiology'
  AND a.appointment_time >= TO_TIMESTAMP_TZ('2026-10-01 00:00:00 UTC', 'YYYY-MM-DD HH24:MI:SS TZR')
GROUP BY a.department, EXTRACT(HOUR FROM a.check_in_time);

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY('PLAN_TABLE', 'WAIT_BASELINE', 'TYPICAL'));

-- Step 2: Create Covering & Filter Indexes
-- CREATE INDEX idx_perf_appt_dept_time ON APPOINTMENTS (department, appointment_time, check_in_time, appointment_id);
-- CREATE INDEX idx_perf_enc_appt_start ON ENCOUNTERS (appointment_id, start_time);

-- Step 3: Explain Plan for Optimized Query (With Composite Covering Index)
EXPLAIN PLAN SET STATEMENT_ID = 'WAIT_OPTIMIZED' FOR
SELECT /*+ INDEX(a idx_perf_appt_dept_time) INDEX(e idx_perf_enc_appt_start) */
    a.department,
    EXTRACT(HOUR FROM a.check_in_time) AS arrival_hour,
    COUNT(*) AS total_patients,
    ROUND(AVG(
        EXTRACT(DAY FROM (e.start_time - a.check_in_time)) * 1440 +
        EXTRACT(HOUR FROM (e.start_time - a.check_in_time)) * 60 +
        EXTRACT(MINUTE FROM (e.start_time - a.check_in_time))
    ), 1) AS avg_wait_minutes
FROM APPOINTMENTS a
JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
WHERE a.check_in_time IS NOT NULL
  AND a.department = 'Cardiology'
  AND a.appointment_time >= TO_TIMESTAMP_TZ('2026-10-01 00:00:00 UTC', 'YYYY-MM-DD HH24:MI:SS TZR')
GROUP BY a.department, EXTRACT(HOUR FROM a.check_in_time);

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY('PLAN_TABLE', 'WAIT_OPTIMIZED', 'TYPICAL'));
