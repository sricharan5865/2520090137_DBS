-- ====================================================================
-- DATABASE VIEWS FOR REPORTING & 360-DEGREE ANALYTICS
-- ====================================================================

-- 1. Patient 360 Comprehensive Medical Overview
CREATE OR REPLACE VIEW v_patient_360 AS
SELECT 
    p.patient_id,
    p.full_name AS patient_name,
    p.date_of_birth,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.date_of_birth)) AS age_years,
    p.gender,
    p.phone,
    p.email,
    p.blood_group,
    p.emergency_contact,
    -- Latest Assessment
    ma.assessment_id AS latest_assessment_id,
    ma.bp AS latest_bp,
    ma.bgr AS latest_bgr,
    ma.sc AS latest_sc,
    ma.hemo AS latest_hemo,
    ma.created_at AS assessment_date,
    -- Latest Prediction
    pr.prediction_id AS latest_prediction_id,
    pr.prediction_result AS latest_prediction,
    pr.probability AS latest_probability,
    pr.risk_level AS latest_risk_level,
    pr.created_at AS prediction_date,
    -- Counts
    (SELECT COUNT(*) FROM appointments a WHERE a.patient_id = p.patient_id) AS total_appointments,
    (SELECT COUNT(*) FROM laboratory_tests lt WHERE lt.patient_id = p.patient_id) AS total_lab_tests,
    (SELECT COUNT(*) FROM prediction_records pr2 WHERE pr2.patient_id = p.patient_id) AS total_predictions
FROM patients p
LEFT JOIN LATERAL (
    SELECT * FROM medical_assessments 
    WHERE patient_id = p.patient_id 
    ORDER BY created_at DESC LIMIT 1
) ma ON TRUE
LEFT JOIN LATERAL (
    SELECT * FROM prediction_records 
    WHERE patient_id = p.patient_id 
    ORDER BY created_at DESC LIMIT 1
) pr ON TRUE;

-- 2. Doctor Workload and Active Patient Overview
CREATE OR REPLACE VIEW v_doctor_workload AS
SELECT 
    d.doctor_id,
    d.full_name AS doctor_name,
    d.specialization,
    d.department,
    COUNT(DISTINCT a.appointment_id) AS total_appointments,
    COUNT(DISTINCT CASE WHEN a.status = 'Requested' THEN a.appointment_id END) AS pending_appointments,
    COUNT(DISTINCT CASE WHEN a.status = 'Confirmed' THEN a.appointment_id END) AS confirmed_appointments,
    COUNT(DISTINCT CASE WHEN a.status = 'Completed' THEN a.appointment_id END) AS completed_appointments,
    COUNT(DISTINCT pr.prediction_id) AS total_predictions_reviewed,
    COUNT(DISTINCT cn.note_id) AS total_clinical_notes_written
FROM doctors d
LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
LEFT JOIN prediction_records pr ON d.doctor_id = pr.doctor_id
LEFT JOIN clinical_notes cn ON d.doctor_id = cn.doctor_id
GROUP BY d.doctor_id, d.full_name, d.specialization, d.department;

-- 3. Staff Laboratory Processing Queue
CREATE OR REPLACE VIEW v_lab_queue AS
SELECT 
    lt.test_id,
    lt.patient_id,
    p.full_name AS patient_name,
    p.phone AS patient_phone,
    lt.test_name,
    lt.sample_type,
    lt.status,
    lt.test_date,
    lt.staff_id,
    s.full_name AS assigned_staff_name,
    d.full_name AS requesting_doctor_name,
    COUNT(lr.result_id) AS recorded_parameters_count,
    COUNT(CASE WHEN lr.abnormal_status != 'Normal' THEN 1 END) AS abnormal_parameters_count
FROM laboratory_tests lt
JOIN patients p ON lt.patient_id = p.patient_id
LEFT JOIN staff s ON lt.staff_id = s.staff_id
LEFT JOIN doctors d ON lt.doctor_id = d.doctor_id
LEFT JOIN laboratory_results lr ON lt.test_id = lr.test_id
GROUP BY lt.test_id, lt.patient_id, p.full_name, p.phone, lt.test_name, lt.sample_type, lt.status, lt.test_date, lt.staff_id, s.full_name, d.full_name;

-- 4. CKD Risk Prediction Analytics View
CREATE OR REPLACE VIEW v_prediction_analytics AS
SELECT 
    pr.prediction_id,
    pr.patient_id,
    p.full_name AS patient_name,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.date_of_birth)) AS patient_age,
    p.gender,
    pr.model_name,
    pr.model_version,
    pr.prediction_result,
    pr.probability,
    pr.risk_level,
    d.full_name AS reviewing_doctor,
    pr.created_at AS prediction_timestamp
FROM prediction_records pr
JOIN patients p ON pr.patient_id = p.patient_id
LEFT JOIN doctors d ON pr.doctor_id = d.doctor_id;
