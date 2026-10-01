-- ====================================================================
-- DEMONSTRATION SQL QUERIES FOR DBMS ACADEMIC EVALUATION
-- ====================================================================

-- 1. Patient Appointment History with Doctor and Department Details (JOIN)
SELECT 
    a.appointment_id,
    p.patient_id,
    p.full_name AS patient_name,
    d.doctor_id,
    d.full_name AS doctor_name,
    d.specialization,
    a.preferred_date,
    a.preferred_time,
    a.reason_for_visit,
    a.status,
    a.created_at
FROM appointments a
INNER JOIN patients p ON a.patient_id = p.patient_id
INNER JOIN doctors d ON a.doctor_id = d.doctor_id
WHERE p.patient_id = 'PAT-001'
ORDER BY a.preferred_date DESC;

-- 2. Doctor's Scheduled Appointments Filtered by Date & Status
SELECT 
    a.appointment_id,
    a.preferred_date,
    a.preferred_time,
    p.patient_id,
    p.full_name AS patient_name,
    p.phone,
    p.gender,
    a.reason_for_visit,
    a.status
FROM appointments a
JOIN patients p ON a.patient_id = p.patient_id
WHERE a.doctor_id = 'DOC-101'
  AND a.status IN ('Confirmed', 'Requested')
ORDER BY a.preferred_date ASC, a.preferred_time ASC;

-- 3. Patient Laboratory Reports & Biomarkers with Abnormal Flags (Aggregation & Subquery)
SELECT 
    lt.test_id,
    lt.test_name,
    lt.sample_type,
    lt.test_date,
    lt.status AS test_status,
    s.full_name AS technician_name,
    lr.parameter_name,
    lr.test_value,
    lr.unit,
    lr.reference_range,
    lr.abnormal_status
FROM laboratory_tests lt
LEFT JOIN staff s ON lt.staff_id = s.staff_id
LEFT JOIN laboratory_results lr ON lt.test_id = lr.test_id
WHERE lt.patient_id = 'PAT-001'
ORDER BY lt.test_date DESC, lr.parameter_name ASC;

-- 4. Patient Historical CKD Risk Predictions with ML Model Metadata
SELECT 
    pr.prediction_id,
    pr.patient_id,
    p.full_name AS patient_name,
    pr.model_name,
    pr.model_version,
    pr.prediction_result,
    pr.probability,
    pr.risk_level,
    d.full_name AS reviewing_doctor,
    pr.clinical_disclaimer,
    pr.created_at AS prediction_date
FROM prediction_records pr
JOIN patients p ON pr.patient_id = p.patient_id
LEFT JOIN doctors d ON pr.doctor_id = d.doctor_id
WHERE pr.patient_id = 'PAT-001'
ORDER BY pr.created_at DESC;

-- 5. Doctor Workload & Clinical Activity Summary (GROUP BY & Aggregations)
SELECT 
    d.doctor_id,
    d.full_name AS doctor_name,
    d.specialization,
    COUNT(DISTINCT a.appointment_id) AS total_appointments,
    COUNT(DISTINCT CASE WHEN a.status = 'Completed' THEN a.appointment_id END) AS completed_appointments,
    COUNT(DISTINCT CASE WHEN a.status = 'Confirmed' THEN a.appointment_id END) AS upcoming_appointments,
    COUNT(DISTINCT pr.prediction_id) AS total_ml_predictions_evaluated,
    COUNT(DISTINCT cn.note_id) AS total_clinical_notes_written
FROM doctors d
LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
LEFT JOIN prediction_records pr ON d.doctor_id = pr.doctor_id
LEFT JOIN clinical_notes cn ON d.doctor_id = cn.doctor_id
GROUP BY d.doctor_id, d.full_name, d.specialization;

-- 6. Overall System Appointment Statistics by Department and Status
SELECT 
    a.department,
    a.status,
    COUNT(a.appointment_id) AS count,
    ROUND(COUNT(a.appointment_id) * 100.0 / SUM(COUNT(a.appointment_id)) OVER(), 2) AS percentage_of_total
FROM appointments a
GROUP BY a.department, a.status
ORDER BY a.department, count DESC;

-- 7. CKD Risk Prediction Distribution & Average Probability by Model
SELECT 
    pr.model_name,
    pr.prediction_result,
    pr.risk_level,
    COUNT(*) AS total_cases,
    ROUND(AVG(pr.probability), 4) AS average_probability,
    MIN(pr.probability) AS min_probability,
    MAX(pr.probability) AS max_probability
FROM prediction_records pr
GROUP BY pr.model_name, pr.prediction_result, pr.risk_level
ORDER BY pr.model_name, total_cases DESC;

-- 8. Staff Pending Laboratory Processing Queue
SELECT 
    lt.test_id,
    lt.patient_id,
    p.full_name AS patient_name,
    p.phone AS contact_phone,
    lt.test_name,
    lt.sample_type,
    lt.test_date,
    lt.status,
    d.full_name AS ordering_doctor
FROM laboratory_tests lt
JOIN patients p ON lt.patient_id = p.patient_id
LEFT JOIN doctors d ON lt.doctor_id = d.doctor_id
WHERE lt.status IN ('Requested', 'Sample Collected', 'Processing')
ORDER BY lt.test_date ASC;
