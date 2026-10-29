-- ============================================================================
-- Report 06: Order Turnaround Time (TAT) Operational Performance
-- Business Question:
--   What is the laboratory turnaround time (hours between order placement and
--   result completion) aggregated by order code and priority?
-- Relevant Tables: ORDERS, RESULTS
-- ============================================================================

WITH tat_metrics AS (
    SELECT 
        o.order_code,
        o.order_name,
        o.priority,
        ROUND(
            EXTRACT(DAY FROM (o.completed_at - o.ordered_at)) * 24 +
            EXTRACT(HOUR FROM (o.completed_at - o.ordered_at)) +
            EXTRACT(MINUTE FROM (o.completed_at - o.ordered_at)) / 60,
            2
        ) AS turnaround_hours
    FROM ORDERS o
    WHERE o.order_status = 'COMPLETED'
      AND o.completed_at IS NOT NULL
      AND (:p_start_date IS NULL OR TRUNC(CAST(o.ordered_at AS DATE)) >= TO_DATE(:p_start_date, 'YYYY-MM-DD'))
      AND (:p_end_date IS NULL OR TRUNC(CAST(o.ordered_at AS DATE)) <= TO_DATE(:p_end_date, 'YYYY-MM-DD'))
)
SELECT 
    order_code,
    order_name,
    priority,
    COUNT(*) AS total_completed_orders,
    ROUND(AVG(turnaround_hours), 2) AS avg_turnaround_hours,
    MIN(turnaround_hours) AS min_turnaround_hours,
    MAX(turnaround_hours) AS max_turnaround_hours,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY turnaround_hours), 2) AS median_turnaround_hours
FROM tat_metrics
GROUP BY order_code, order_name, priority
ORDER BY avg_turnaround_hours DESC;
