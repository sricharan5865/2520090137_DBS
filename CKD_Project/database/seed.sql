-- ====================================================================
-- DATABASE SEED DATA (Demo Users, Profiles, Records)
-- ====================================================================

-- 1. Insert Roles
INSERT INTO roles (role_name, description) VALUES
('ADMIN', 'System Administrator with full management & analytics access'),
('DOCTOR', 'Licensed Medical Practitioner / Nephrologist'),
('STAFF', 'Clinical Laboratory Technologist & Healthcare Staff'),
('PATIENT', 'Registered Patient seeking medical review and lab analysis')
ON CONFLICT (role_name) DO NOTHING;

-- 2. Insert Users
-- Passwords:
-- Admin@123   -> $2b$12$aV2bHGuW6eCnUZ87fv2YpOD1TWDEVwzJpSNxlay1NevVEbHsPa8uS
-- Doctor@123  -> $2b$12$vwcOvPZGNBolOz64WhP/j.uJbOhDazftTs2iD0zDL3vSHTJPlz0Hu
-- Staff@123   -> $2b$12$xItXwhekwwS4JdfWhPNG3uR/.fQwH0X4AdjtWuRGLURaYWH/VrYm.
-- Patient@123 -> $2b$12$WvyanYXZFOovmU.xEzW5KeQXT29o/UaZQ3NSOxa7ib1E9uVTbfpfe

INSERT INTO users (user_id, username, email, password_hash, role_name, is_active) VALUES
(1, 'admin', 'admin@hospital.com', '$2b$12$aV2bHGuW6eCnUZ87fv2YpOD1TWDEVwzJpSNxlay1NevVEbHsPa8uS', 'ADMIN', true),
(2, 'dr_sarah', 'doctor.sarah@hospital.com', '$2b$12$vwcOvPZGNBolOz64WhP/j.uJbOhDazftTs2iD0zDL3vSHTJPlz0Hu', 'DOCTOR', true),
(3, 'dr_arun', 'doctor.arun@hospital.com', '$2b$12$vwcOvPZGNBolOz64WhP/j.uJbOhDazftTs2iD0zDL3vSHTJPlz0Hu', 'DOCTOR', true),
(4, 'staff_james', 'staff.james@hospital.com', '$2b$12$xItXwhekwwS4JdfWhPNG3uR/.fQwH0X4AdjtWuRGLURaYWH/VrYm.', 'STAFF', true),
(5, 'patient_john', 'patient.john@hospital.com', '$2b$12$WvyanYXZFOovmU.xEzW5KeQXT29o/UaZQ3NSOxa7ib1E9uVTbfpfe', 'PATIENT', true),
(6, 'patient_elena', 'patient.elena@hospital.com', '$2b$12$WvyanYXZFOovmU.xEzW5KeQXT29o/UaZQ3NSOxa7ib1E9uVTbfpfe', 'PATIENT', true)
ON CONFLICT (user_id) DO NOTHING;

-- 3. Insert Doctors
INSERT INTO doctors (doctor_id, user_id, full_name, specialization, department, license_number, phone, email, consulting_hours) VALUES
('DOC-101', 2, 'Dr. Sarah Jenkins, MD', 'Chief Nephrologist', 'Department of Renal Medicine', 'MED-LIC-88291', '+1 (555) 234-5678', 'doctor.sarah@hospital.com', '09:00 AM - 04:30 PM'),
('DOC-102', 3, 'Dr. Arun Patel, DM', 'Consultant Nephrologist & Transplant Specialist', 'Department of Renal Medicine', 'MED-LIC-99104', '+1 (555) 345-6789', 'doctor.arun@hospital.com', '10:00 AM - 06:00 PM')
ON CONFLICT (doctor_id) DO NOTHING;

-- 4. Insert Staff
INSERT INTO staff (staff_id, user_id, full_name, department, designation, phone, email) VALUES
('STF-501', 4, 'James Wilson, MLS', 'Central Diagnostic Laboratory', 'Senior Clinical Pathology Technologist', '+1 (555) 456-7890', 'staff.james@hospital.com')
ON CONFLICT (staff_id) DO NOTHING;

-- 5. Insert Patients
INSERT INTO patients (patient_id, user_id, full_name, date_of_birth, gender, phone, email, address, emergency_contact, blood_group) VALUES
('PAT-001', 5, 'Johnathan Miller', '1968-05-14', 'Male', '+1 (555) 678-1234', 'patient.john@hospital.com', '742 Evergreen Terrace, Springfield', '+1 (555) 999-1122 (Wife)', 'O+'),
('PAT-002', 6, 'Elena Rostova', '1982-11-20', 'Female', '+1 (555) 789-5678', 'patient.elena@hospital.com', '108 Beacon Hill Ave, Boston, MA', '+1 (555) 888-3344 (Brother)', 'A+')
ON CONFLICT (patient_id) DO NOTHING;

-- 6. Insert Doctor-Patient Assignments
INSERT INTO doctor_patient_assignments (patient_id, doctor_id, status) VALUES
('PAT-001', 'DOC-101', 'Active'),
('PAT-002', 'DOC-101', 'Active')
ON CONFLICT (patient_id, doctor_id) DO NOTHING;

-- 7. Insert Medical Assessments (Patient John has high-risk CKD markers, Elena has normal markers)
INSERT INTO medical_assessments (
    assessment_id, patient_id, age, bp, sg, al, su, rbc, pc, pcc, ba,
    bgr, bu, sc, sod, pot, hemo, pcv, wc, rc, htn, dm, cad, appet, pe, ane, notes
) VALUES
(1, 'PAT-001', 58.0, 90.0, 1.010, 3.0, 1.0, 'abnormal', 'abnormal', 'present', 'notpresent',
 160.0, 68.0, 3.4, 131.0, 5.2, 9.4, 29.0, 9800.0, 3.5, 'yes', 'yes', 'no', 'poor', 'yes', 'yes',
 'Patient reports chronic fatigue, bilateral ankle swelling, and uncontrolled hypertension.'),
(2, 'PAT-002', 43.0, 70.0, 1.025, 0.0, 0.0, 'normal', 'normal', 'notpresent', 'notpresent',
 98.0, 22.0, 0.9, 140.0, 4.2, 14.5, 45.0, 6800.0, 4.9, 'no', 'no', 'no', 'good', 'no', 'no',
 'Routine annual health checkup. Patient is asymptomatic with good renal indicators.')
ON CONFLICT (assessment_id) DO NOTHING;

-- 8. Insert Appointments
INSERT INTO appointments (
    appointment_id, patient_id, doctor_id, department, preferred_date, preferred_time, reason_for_visit, status
) VALUES
(1, 'PAT-001', 'DOC-101', 'Nephrology', CURRENT_DATE + INTERVAL '1 day', '10:00 AM', 'Follow-up on elevated serum creatinine and edema evaluation', 'Confirmed'),
(2, 'PAT-002', 'DOC-101', 'Nephrology', CURRENT_DATE + INTERVAL '3 days', '02:30 PM', 'Annual renal wellness screening', 'Requested')
ON CONFLICT (appointment_id) DO NOTHING;

-- 9. Insert Laboratory Tests
INSERT INTO laboratory_tests (
    test_id, patient_id, staff_id, doctor_id, test_name, sample_type, test_date, status, comments
) VALUES
(1, 'PAT-001', 'STF-501', 'DOC-101', 'Comprehensive Renal Function Panel (RFP)', 'Serum & 24hr Urine', CURRENT_TIMESTAMP - INTERVAL '1 day', 'Verified', 'Marked elevation in BUN and serum creatinine. Moderate proteinuria noted.'),
(2, 'PAT-002', 'STF-501', 'DOC-101', 'Routine Metabolic & Urinalysis Panel', 'Serum & Spot Urine', CURRENT_TIMESTAMP, 'Processing', 'Sample received, running automated spectrometry.')
ON CONFLICT (test_id) DO NOTHING;

-- 10. Insert Laboratory Results for Test 1
INSERT INTO laboratory_results (test_id, parameter_name, parameter_code, test_value, unit, reference_range, abnormal_status) VALUES
(1, 'Serum Creatinine', 'SC', 3.40, 'mg/dL', '0.6 - 1.2', 'High'),
(1, 'Blood Urea Nitrogen', 'BU', 68.0, 'mg/dL', '7 - 20', 'High'),
(1, 'Urine Specific Gravity', 'SG', 1.010, '', '1.015 - 1.025', 'Low'),
(1, 'Hemoglobin', 'HEMO', 9.4, 'g/dL', '13.5 - 17.5', 'Low'),
(1, 'Serum Potassium', 'POT', 5.2, 'mEq/L', '3.5 - 5.0', 'High'),
(1, 'Serum Sodium', 'SOD', 131.0, 'mEq/L', '135 - 145', 'Low');

-- 11. Insert Prediction Records
INSERT INTO prediction_records (
    prediction_id, patient_id, doctor_id, assessment_id, model_name, model_version,
    prediction_result, probability, risk_level, top_factors_json, shap_explanation_json
) VALUES
(1, 'PAT-001', 'DOC-101', 1, 'XGBoost', '1.0.0', 'CKD Detected', 0.9840, 'High Risk',
 '[{"feature": "hemo", "friendly_name": "Hemoglobin Level", "shap_value": 1.43, "risk_impact": "Increases CKD Risk"}, {"feature": "sc", "friendly_name": "Serum Creatinine", "shap_value": 0.92, "risk_impact": "Increases CKD Risk"}, {"feature": "al", "friendly_name": "Albuminuria", "shap_value": 0.90, "risk_impact": "Increases CKD Risk"}]'::jsonb,
 '{"base_value": -0.42, "model": "XGBoost Classifier v1.0.0"}'::jsonb
) ON CONFLICT (prediction_id) DO NOTHING;

-- 12. Insert Clinical Notes
INSERT INTO clinical_notes (
    note_id, patient_id, doctor_id, appointment_id, prediction_id, clinical_summary, diagnosis, treatment_plan, prescriptions, follow_up_date
) VALUES
(1, 'PAT-001', 'DOC-101', 1, 1,
 'Patient presents with stage 3b/4 chronic kidney disease indicators, microalbuminuria, and secondary anemia.',
 'Chronic Kidney Disease (Stage 3b-4) with Renal Anemia & Secondary Hypertension',
 '1. Low sodium & low protein dietary regimen.\n2. Blood pressure strict control (<130/80 mmHg).\n3. Erythropoietin therapy initiation.\n4. Nephrology consult in 4 weeks.',
 'Losartan 50mg OD, Torsemide 10mg OD, Calcium Acetate 667mg with meals, Darbepoetin alfa weekly',
 CURRENT_DATE + INTERVAL '28 days'
) ON CONFLICT (note_id) DO NOTHING;

-- 13. Insert Initial Notifications
INSERT INTO notifications (recipient_user_id, title, message, category, link_url) VALUES
(5, 'Welcome to CKD SmartCare', 'Your patient portal is active. Please complete your medical assessment form.', 'System', '/patient/index.html'),
(2, 'Patient Record Ready for Review', 'Patient Johnathan Miller (PAT-001) has verified lab tests and CKD analysis pending.', 'Clinical', '/doctor/index.html'),
(4, 'New Lab Request', 'Metabolic & Urinalysis Panel requested for Patient Elena Rostova (PAT-002).', 'Laboratory', '/staff/index.html'),
(1, 'System Initialized', 'Database schema, seed data, and ML pipeline v1.0.0 active.', 'System', '/admin/index.html');

-- Reset sequences for auto-increment IDs
SELECT setval(pg_get_serial_sequence('users', 'user_id'), COALESCE(MAX(user_id), 1)) FROM users;
SELECT setval(pg_get_serial_sequence('appointments', 'appointment_id'), COALESCE(MAX(appointment_id), 1)) FROM appointments;
SELECT setval(pg_get_serial_sequence('medical_assessments', 'assessment_id'), COALESCE(MAX(assessment_id), 1)) FROM medical_assessments;
SELECT setval(pg_get_serial_sequence('laboratory_tests', 'test_id'), COALESCE(MAX(test_id), 1)) FROM laboratory_tests;
SELECT setval(pg_get_serial_sequence('laboratory_results', 'result_id'), COALESCE(MAX(result_id), 1)) FROM laboratory_results;
SELECT setval(pg_get_serial_sequence('prediction_records', 'prediction_id'), COALESCE(MAX(prediction_id), 1)) FROM prediction_records;
SELECT setval(pg_get_serial_sequence('clinical_notes', 'note_id'), COALESCE(MAX(note_id), 1)) FROM clinical_notes;
SELECT setval(pg_get_serial_sequence('notifications', 'notification_id'), COALESCE(MAX(notification_id), 1)) FROM notifications;
