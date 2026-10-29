-- ============================================================================
-- CareFlow Healthcare Operations Platform
-- Oracle PL/SQL Package Body: CAREFLOW_WORKFLOW_PKG
-- database/packages/careflow_workflow_pkg.pkb
-- ============================================================================

CREATE OR REPLACE PACKAGE BODY careflow_workflow_pkg AS

    -- Private helper to record audit entry
    PROCEDURE log_audit (
        p_entity_type   IN VARCHAR2,
        p_entity_id     IN NUMBER,
        p_action        IN VARCHAR2,
        p_actor         IN VARCHAR2,
        p_prev_state    IN CLOB,
        p_new_state     IN CLOB,
        p_reason        IN VARCHAR2
    ) IS
    BEGIN
        INSERT INTO AUDIT_LOG (
            entity_type, entity_id, action, actor, 
            previous_state, new_state, correlation_id, reason, changed_at
        ) VALUES (
            p_entity_type, p_entity_id, p_action, p_actor,
            p_prev_state, p_new_state, SYS_GUID(), p_reason, SYSTIMESTAMP
        );
    END log_audit;

    -- Private helper to record status history
    PROCEDURE log_status_history (
        p_entity_type   IN VARCHAR2,
        p_entity_id     IN NUMBER,
        p_from_status   IN VARCHAR2,
        p_to_status     IN VARCHAR2,
        p_actor         IN VARCHAR2,
        p_reason        IN VARCHAR2
    ) IS
    BEGIN
        INSERT INTO STATUS_HISTORY (
            entity_type, entity_id, from_status, to_status, actor, reason, changed_at
        ) VALUES (
            p_entity_type, p_entity_id, p_from_status, p_to_status, p_actor, p_reason, SYSTIMESTAMP
        );
    END log_status_history;

    -- 1. Check in a scheduled appointment and automatically open an encounter
    PROCEDURE check_in_patient (
        p_appointment_id    IN  NUMBER,
        p_actor             IN  VARCHAR2,
        p_encounter_id      OUT NUMBER
    ) IS
        v_current_status    APPOINTMENTS.status%TYPE;
        v_patient_id        APPOINTMENTS.patient_id%TYPE;
        v_department        APPOINTMENTS.department%TYPE;
        v_provider          APPOINTMENTS.provider_name%TYPE;
        v_now               TIMESTAMP WITH TIME ZONE := SYSTIMESTAMP;
    BEGIN
        -- Lock row for concurrency safety
        BEGIN
            SELECT status, patient_id, department, provider_name
            INTO v_current_status, v_patient_id, v_department, v_provider
            FROM APPOINTMENTS
            WHERE appointment_id = p_appointment_id
            FOR UPDATE;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                raise_application_error(c_err_not_found, 'Appointment ID ' || p_appointment_id || ' not found.');
        END;

        -- Validate status transition: Only SCHEDULED can be CHECKED_IN
        IF v_current_status != 'SCHEDULED' THEN
            raise_application_error(
                c_err_invalid_transition,
                'Cannot check in appointment. Current status is ' || v_current_status || '. Expected SCHEDULED.'
            );
        END IF;

        -- Update appointment
        UPDATE APPOINTMENTS
        SET status = 'CHECKED_IN',
            check_in_time = v_now,
            updated_at = v_now
        WHERE appointment_id = p_appointment_id;

        -- Record appointment status history and audit
        log_status_history('APPOINTMENT', p_appointment_id, v_current_status, 'CHECKED_IN', p_actor, 'Patient arrived at clinic');
        log_audit('APPOINTMENT', p_appointment_id, 'CHECK_IN', p_actor, '{"status": "' || v_current_status || '"}', '{"status": "CHECKED_IN", "check_in_time": "' || TO_CHAR(v_now, 'YYYY-MM-DD"T"HH24:MI:SS') || '"}', 'Clinic reception check-in');

        -- Atomically create the initial encounter
        INSERT INTO ENCOUNTERS (
            patient_id, appointment_id, encounter_type, department,
            provider_name, status, start_time, chief_complaint, created_at, updated_at
        ) VALUES (
            v_patient_id, p_appointment_id, 'OUTPATIENT', v_department,
            v_provider, 'OPEN', v_now, 'Routine visit initiated upon check-in', v_now, v_now
        ) RETURNING encounter_id INTO p_encounter_id;

        -- Record encounter status history and audit
        log_status_history('ENCOUNTER', p_encounter_id, NULL, 'OPEN', p_actor, 'Auto-generated on appointment check-in');
        log_audit('ENCOUNTER', p_encounter_id, 'CREATE_FROM_CHECKIN', p_actor, NULL, '{"status": "OPEN", "appointment_id": ' || p_appointment_id || '}', 'Encounter opened from check-in');

    EXCEPTION
        WHEN OTHERS THEN
            -- In real PL/SQL caller handles commit/rollback or package rolls back
            RAISE;
    END check_in_patient;

    -- 2. Complete an encounter with workflow safety enforcement
    PROCEDURE complete_encounter (
        p_encounter_id      IN NUMBER,
        p_actor             IN VARCHAR2,
        p_clinical_notes    IN VARCHAR2 DEFAULT NULL
    ) IS
        v_current_status    ENCOUNTERS.status%TYPE;
        v_appointment_id    ENCOUNTERS.appointment_id%TYPE;
        v_pending_count     NUMBER := 0;
        v_now               TIMESTAMP WITH TIME ZONE := SYSTIMESTAMP;
    BEGIN
        -- Lock row
        BEGIN
            SELECT status, appointment_id
            INTO v_current_status, v_appointment_id
            FROM ENCOUNTERS
            WHERE encounter_id = p_encounter_id
            FOR UPDATE;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                raise_application_error(c_err_not_found, 'Encounter ID ' || p_encounter_id || ' not found.');
        END;

        IF v_current_status = 'COMPLETED' THEN
            raise_application_error(c_err_invalid_transition, 'Encounter is already COMPLETED.');
        ELSIF v_current_status = 'CANCELLED' THEN
            raise_application_error(c_err_invalid_transition, 'Cannot complete a CANCELLED encounter.');
        END IF;

        -- Business Rule: Check for pending clinical orders
        SELECT COUNT(*)
        INTO v_pending_count
        FROM ORDERS
        WHERE encounter_id = p_encounter_id
          AND order_status IN ('ORDERED', 'IN_PROGRESS');

        IF v_pending_count > 0 THEN
            raise_application_error(
                c_err_pending_orders,
                'Encounter cannot be completed: ' || v_pending_count || ' order(s) remain pending results.'
            );
        END IF;

        -- Update encounter
        UPDATE ENCOUNTERS
        SET status = 'COMPLETED',
            end_time = v_now,
            clinical_notes = NVL(p_clinical_notes, clinical_notes),
            updated_at = v_now
        WHERE encounter_id = p_encounter_id;

        -- Record status history and audit
        log_status_history('ENCOUNTER', p_encounter_id, v_current_status, 'COMPLETED', p_actor, 'Provider signed off visit');
        log_audit('ENCOUNTER', p_encounter_id, 'COMPLETE', p_actor, '{"status": "' || v_current_status || '"}', '{"status": "COMPLETED"}', 'Clinical signoff');

        -- If linked to an appointment, complete the appointment as well
        IF v_appointment_id IS NOT NULL THEN
            UPDATE APPOINTMENTS
            SET status = 'COMPLETED',
                updated_at = v_now
            WHERE appointment_id = v_appointment_id
              AND status != 'COMPLETED';

            log_status_history('APPOINTMENT', v_appointment_id, 'IN_PROGRESS', 'COMPLETED', p_actor, 'Encounter finished');
        END IF;

    EXCEPTION
        WHEN OTHERS THEN
            RAISE;
    END complete_encounter;

    -- 3. Complete an order and record its lab result atomically
    PROCEDURE complete_order_with_result (
        p_order_id          IN  NUMBER,
        p_result_value      IN  VARCHAR2,
        p_reference_range   IN  VARCHAR2,
        p_unit              IN  VARCHAR2,
        p_abnormal_flag     IN  VARCHAR2,
        p_actor             IN  VARCHAR2,
        p_result_id         OUT NUMBER
    ) IS
        v_current_status    ORDERS.order_status%TYPE;
        v_existing_res      NUMBER := 0;
        v_now               TIMESTAMP WITH TIME ZONE := SYSTIMESTAMP;
    BEGIN
        -- Lock order row
        BEGIN
            SELECT order_status
            INTO v_current_status
            FROM ORDERS
            WHERE order_id = p_order_id
            FOR UPDATE;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                raise_application_error(c_err_not_found, 'Order ID ' || p_order_id || ' not found.');
        END;

        IF v_current_status = 'COMPLETED' THEN
            raise_application_error(c_err_invalid_transition, 'Order is already marked COMPLETED.');
        ELSIF v_current_status = 'CANCELLED' THEN
            raise_application_error(c_err_invalid_transition, 'Cannot attach result to a CANCELLED order.');
        END IF;

        -- Verify result does not exist
        SELECT COUNT(*)
        INTO v_existing_res
        FROM RESULTS
        WHERE order_id = p_order_id;

        IF v_existing_res > 0 THEN
            raise_application_error(c_err_duplicate_result, 'A result already exists for Order ID ' || p_order_id);
        END IF;

        -- Insert Result
        INSERT INTO RESULTS (
            order_id, result_value, reference_range, unit,
            abnormal_flag, result_status, result_time
        ) VALUES (
            p_order_id, p_result_value, p_reference_range, p_unit,
            p_abnormal_flag, 'PENDING_REVIEW', v_now
        ) RETURNING result_id INTO p_result_id;

        -- Update Order to COMPLETED
        UPDATE ORDERS
        SET order_status = 'COMPLETED',
            completed_at = v_now
        WHERE order_id = p_order_id;

        log_status_history('ORDER', p_order_id, v_current_status, 'COMPLETED', p_actor, 'Lab results posted');
        log_audit('ORDER', p_order_id, 'COMPLETE_WITH_RESULT', p_actor, '{"status": "' || v_current_status || '"}', '{"status": "COMPLETED", "result_id": ' || p_result_id || '}', 'Lab interface automated post');

    EXCEPTION
        WHEN OTHERS THEN
            RAISE;
    END complete_order_with_result;

    -- 4. Mark a clinical result as reviewed
    PROCEDURE review_result (
        p_result_id         IN NUMBER,
        p_reviewer          IN VARCHAR2
    ) IS
        v_current_status    RESULTS.result_status%TYPE;
        v_order_id          RESULTS.order_id%TYPE;
        v_now               TIMESTAMP WITH TIME ZONE := SYSTIMESTAMP;
    BEGIN
        BEGIN
            SELECT result_status, order_id
            INTO v_current_status, v_order_id
            FROM RESULTS
            WHERE result_id = p_result_id
            FOR UPDATE;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                raise_application_error(c_err_not_found, 'Result ID ' || p_result_id || ' not found.');
        END;

        IF v_current_status = 'REVIEWED' THEN
            raise_application_error(c_err_invalid_transition, 'Result has already been reviewed.');
        END IF;

        UPDATE RESULTS
        SET result_status = 'REVIEWED',
            reviewed_by = p_reviewer,
            reviewed_at = v_now
        WHERE result_id = p_result_id;

        log_audit('RESULT', p_result_id, 'CLINICAL_REVIEW', p_reviewer, '{"status": "' || v_current_status || '"}', '{"status": "REVIEWED"}', 'Physician signoff');

    EXCEPTION
        WHEN OTHERS THEN
            RAISE;
    END review_result;

    -- 5. Calculate average patient wait time in minutes for a department
    FUNCTION calculate_avg_wait_minutes (
        p_department        IN VARCHAR2,
        p_target_date       IN DATE DEFAULT TRUNC(SYSDATE)
    ) RETURN NUMBER IS
        v_avg_minutes       NUMBER;
    BEGIN
        SELECT NVL(ROUND(AVG(
            EXTRACT(DAY FROM (e.start_time - a.check_in_time)) * 1440 +
            EXTRACT(HOUR FROM (e.start_time - a.check_in_time)) * 60 +
            EXTRACT(MINUTE FROM (e.start_time - a.check_in_time)) +
            EXTRACT(SECOND FROM (e.start_time - a.check_in_time)) / 60
        ), 1), 0)
        INTO v_avg_minutes
        FROM APPOINTMENTS a
        JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id
        WHERE a.department = p_department
          AND TRUNC(CAST(a.appointment_time AS DATE)) = TRUNC(p_target_date)
          AND a.check_in_time IS NOT NULL
          AND e.start_time >= a.check_in_time;

        RETURN v_avg_minutes;
    EXCEPTION
        WHEN OTHERS THEN
            RETURN 0;
    END calculate_avg_wait_minutes;

    -- 6. Calculate turnaround time in hours for an order
    FUNCTION order_turnaround_hours (
        p_order_id          IN NUMBER
    ) RETURN NUMBER IS
        v_hours             NUMBER;
    BEGIN
        SELECT ROUND(
            EXTRACT(DAY FROM (completed_at - ordered_at)) * 24 +
            EXTRACT(HOUR FROM (completed_at - ordered_at)) +
            EXTRACT(MINUTE FROM (completed_at - ordered_at)) / 60,
            2
        )
        INTO v_hours
        FROM ORDERS
        WHERE order_id = p_order_id
          AND completed_at IS NOT NULL;

        RETURN v_hours;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN NULL;
        WHEN OTHERS THEN
            RETURN NULL;
    END order_turnaround_hours;

    -- 7. Execute real-time data quality integrity audit
    PROCEDURE run_data_quality_audit (
        p_detected_count    OUT NUMBER
    ) IS
        v_now               TIMESTAMP WITH TIME ZONE := SYSTIMESTAMP;
        v_count             NUMBER := 0;
    BEGIN
        -- Rule DQ_01: Appointments checked in without check_in_time
        FOR r IN (
            SELECT appointment_id
            FROM APPOINTMENTS
            WHERE status = 'CHECKED_IN' AND check_in_time IS NULL
        ) LOOP
            MERGE INTO DATA_QUALITY_ISSUES dq
            USING DUAL ON (dq.rule_code = 'DQ_MISSING_CHECKIN_TIME' AND dq.entity_id = r.appointment_id)
            WHEN NOT MATCHED THEN
                INSERT (rule_code, severity, affected_entity, entity_id, detection_time, description, investigation_steps, resolution_status)
                VALUES ('DQ_MISSING_CHECKIN_TIME', 'HIGH', 'APPOINTMENT', r.appointment_id, v_now,
                        'Appointment marked CHECKED_IN but check_in_time timestamp is NULL',
                        'Inspect check-in audit logs; backfill arrival timestamp or reset state', 'OPEN');
            v_count := v_count + 1;
        END LOOP;

        -- Rule DQ_02: Completed orders without completed_at
        FOR r IN (
            SELECT order_id
            FROM ORDERS
            WHERE order_status = 'COMPLETED' AND completed_at IS NULL
        ) LOOP
            MERGE INTO DATA_QUALITY_ISSUES dq
            USING DUAL ON (dq.rule_code = 'DQ_MISSING_COMPLETION_TIME' AND dq.entity_id = r.order_id)
            WHEN NOT MATCHED THEN
                INSERT (rule_code, severity, affected_entity, entity_id, detection_time, description, investigation_steps, resolution_status)
                VALUES ('DQ_MISSING_COMPLETION_TIME', 'MEDIUM', 'ORDER', r.order_id, v_now,
                        'Order marked COMPLETED but completed_at timestamp is NULL',
                        'Check associated RESULT result_time and backfill completed_at', 'OPEN');
            v_count := v_count + 1;
        END LOOP;

        -- Rule DQ_03: Completed encounters with active pending orders
        FOR r IN (
            SELECT e.encounter_id, COUNT(o.order_id) as pending_cnt
            FROM ENCOUNTERS e
            JOIN ORDERS o ON e.encounter_id = o.encounter_id
            WHERE e.status = 'COMPLETED'
              AND o.order_status IN ('ORDERED', 'IN_PROGRESS')
            GROUP BY e.encounter_id
        ) LOOP
            MERGE INTO DATA_QUALITY_ISSUES dq
            USING DUAL ON (dq.rule_code = 'DQ_COMPLETED_ENC_WITH_PENDING_ORDERS' AND dq.entity_id = r.encounter_id)
            WHEN NOT MATCHED THEN
                INSERT (rule_code, severity, affected_entity, entity_id, detection_time, description, investigation_steps, resolution_status)
                VALUES ('DQ_COMPLETED_ENC_WITH_PENDING_ORDERS', 'CRITICAL', 'ENCOUNTER', r.encounter_id, v_now,
                        'Encounter marked COMPLETED despite having ' || r.pending_cnt || ' pending order(s)',
                        'Determine whether orders were orphaned, cancelled, or if clinical review was missed', 'OPEN');
            v_count := v_count + 1;
        END LOOP;

        -- Rule DQ_04: Encounters with end_time before start_time
        FOR r IN (
            SELECT encounter_id
            FROM ENCOUNTERS
            WHERE end_time < start_time
        ) LOOP
            MERGE INTO DATA_QUALITY_ISSUES dq
            USING DUAL ON (dq.rule_code = 'DQ_INVALID_TIMESTAMP_SEQUENCE' AND dq.entity_id = r.encounter_id)
            WHEN NOT MATCHED THEN
                INSERT (rule_code, severity, affected_entity, entity_id, detection_time, description, investigation_steps, resolution_status)
                VALUES ('DQ_INVALID_TIMESTAMP_SEQUENCE', 'CRITICAL', 'ENCOUNTER', r.encounter_id, v_now,
                        'Encounter end_time precedes start_time',
                        'Inspect server clocks, time zones, or audit trail to adjust end timestamp', 'OPEN');
            v_count := v_count + 1;
        END LOOP;

        -- Rule DQ_05: Results without valid order reference
        FOR r IN (
            SELECT res.result_id
            FROM RESULTS res
            LEFT JOIN ORDERS ord ON res.order_id = ord.order_id
            WHERE ord.order_id IS NULL
        ) LOOP
            MERGE INTO DATA_QUALITY_ISSUES dq
            USING DUAL ON (dq.rule_code = 'DQ_ORPHANED_RESULT' AND dq.entity_id = r.result_id)
            WHEN NOT MATCHED THEN
                INSERT (rule_code, severity, affected_entity, entity_id, detection_time, description, investigation_steps, resolution_status)
                VALUES ('DQ_ORPHANED_RESULT', 'CRITICAL', 'RESULT', r.result_id, v_now,
                        'Result record exists without a corresponding Order record',
                        'Investigate foreign key integrity or orphaned test results', 'OPEN');
            v_count := v_count + 1;
        END LOOP;

        SELECT COUNT(*)
        INTO p_detected_count
        FROM DATA_QUALITY_ISSUES
        WHERE resolution_status IN ('OPEN', 'INVESTIGATING');

    END run_data_quality_audit;

END careflow_workflow_pkg;
/
