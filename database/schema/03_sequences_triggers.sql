-- ============================================================================
-- CareFlow Healthcare Operations Platform
-- Oracle Database Free (23ai / 21c) Triggers & Helper Functions
-- 03_sequences_triggers.sql
-- ============================================================================

-- Trigger: Automatically update updated_at on PATIENTS
CREATE OR REPLACE TRIGGER trg_patients_updated_at
BEFORE UPDATE ON PATIENTS
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

-- Trigger: Automatically update updated_at on APPOINTMENTS
CREATE OR REPLACE TRIGGER trg_appts_updated_at
BEFORE UPDATE ON APPOINTMENTS
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

-- Trigger: Automatically update updated_at on ENCOUNTERS
CREATE OR REPLACE TRIGGER trg_enc_updated_at
BEFORE UPDATE ON ENCOUNTERS
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/
