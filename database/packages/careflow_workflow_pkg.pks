-- ============================================================================
-- CareFlow Healthcare Operations Platform
-- Oracle PL/SQL Package Specification: CAREFLOW_WORKFLOW_PKG
-- database/packages/careflow_workflow_pkg.pks
-- ============================================================================

CREATE OR REPLACE PACKAGE careflow_workflow_pkg AS

    -- Custom Application Error Codes
    c_err_not_found             CONSTANT NUMBER := -20001;
    c_err_invalid_transition    CONSTANT NUMBER := -20002;
    c_err_pending_orders        CONSTANT NUMBER := -20003;
    c_err_duplicate_result      CONSTANT NUMBER := -20004;
    c_err_validation_failed     CONSTANT NUMBER := -20005;

    -- Exceptions
    e_not_found                 EXCEPTION;
    e_invalid_transition        EXCEPTION;
    e_pending_orders            EXCEPTION;
    e_duplicate_result          EXCEPTION;
    e_validation_failed         EXCEPTION;

    PRAGMA EXCEPTION_INIT(e_not_found, -20001);
    PRAGMA EXCEPTION_INIT(e_invalid_transition, -20002);
    PRAGMA EXCEPTION_INIT(e_pending_orders, -20003);
    PRAGMA EXCEPTION_INIT(e_duplicate_result, -20004);
    PRAGMA EXCEPTION_INIT(e_validation_failed, -20005);

    -- 1. Check in a scheduled appointment and automatically open an encounter
    PROCEDURE check_in_patient (
        p_appointment_id    IN  NUMBER,
        p_actor             IN  VARCHAR2,
        p_encounter_id      OUT NUMBER
    );

    -- 2. Complete an encounter with workflow safety enforcement
    PROCEDURE complete_encounter (
        p_encounter_id      IN NUMBER,
        p_actor             IN VARCHAR2,
        p_clinical_notes    IN VARCHAR2 DEFAULT NULL
    );

    -- 3. Complete an order and record its lab result atomically
    PROCEDURE complete_order_with_result (
        p_order_id          IN  NUMBER,
        p_result_value      IN  VARCHAR2,
        p_reference_range   IN  VARCHAR2,
        p_unit              IN  VARCHAR2,
        p_abnormal_flag     IN  VARCHAR2,
        p_actor             IN  VARCHAR2,
        p_result_id         OUT NUMBER
    );

    -- 4. Mark a clinical result as reviewed
    PROCEDURE review_result (
        p_result_id         IN NUMBER,
        p_reviewer          IN VARCHAR2
    );

    -- 5. Calculate average patient wait time in minutes for a department
    FUNCTION calculate_avg_wait_minutes (
        p_department        IN VARCHAR2,
        p_target_date       IN DATE DEFAULT TRUNC(SYSDATE)
    ) RETURN NUMBER;

    -- 6. Calculate turnaround time in hours for an order
    FUNCTION order_turnaround_hours (
        p_order_id          IN NUMBER
    ) RETURN NUMBER;

    -- 7. Execute real-time data quality integrity audit
    PROCEDURE run_data_quality_audit (
        p_detected_count    OUT NUMBER
    );

END careflow_workflow_pkg;
/
