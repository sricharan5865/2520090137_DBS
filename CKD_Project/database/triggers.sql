-- ====================================================================
-- DATABASE TRIGGERS (Automated Audit Logging & Workflow Actions)
-- ====================================================================

-- 1. Trigger Function for Prediction Audit Logging
CREATE OR REPLACE FUNCTION trg_log_prediction()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        user_id, role_name, action, resource, resource_id, details, status
    ) VALUES (
        (SELECT user_id FROM doctors WHERE doctor_id = NEW.doctor_id),
        'DOCTOR',
        'RUN_CKD_PREDICTION',
        'prediction_records',
        NEW.prediction_id::text,
        json_build_object(
            'patient_id', NEW.patient_id,
            'model', NEW.model_name,
            'result', NEW.prediction_result,
            'probability', NEW.probability,
            'risk_level', NEW.risk_level
        )::jsonb,
        'SUCCESS'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prediction_audit ON prediction_records;
CREATE TRIGGER trg_prediction_audit
AFTER INSERT ON prediction_records
FOR EACH ROW
EXECUTE FUNCTION trg_log_prediction();


-- 2. Trigger Function for User Account Audit Logging
CREATE OR REPLACE FUNCTION trg_log_user_creation()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        user_id, role_name, action, resource, resource_id, details, status
    ) VALUES (
        NEW.user_id,
        NEW.role_name,
        'USER_REGISTERED',
        'users',
        NEW.user_id::text,
        json_build_object(
            'username', NEW.username,
            'email', NEW.email,
            'role', NEW.role_name
        )::jsonb,
        'SUCCESS'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_user_creation_audit ON users;
CREATE TRIGGER trg_user_creation_audit
AFTER INSERT ON users
FOR EACH ROW
EXECUTE FUNCTION trg_log_user_creation();
