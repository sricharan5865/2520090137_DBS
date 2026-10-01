-- ====================================================================
-- DATABASE PERFORMANCE INDEXES
-- ====================================================================

-- Users & Auth Lookup
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_name);

-- Patients Identity & Demographics
CREATE INDEX IF NOT EXISTS idx_patients_user_id ON patients(user_id);
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);

-- Doctors & Staff
CREATE INDEX IF NOT EXISTS idx_doctors_user_id ON doctors(user_id);
CREATE INDEX IF NOT EXISTS idx_doctors_specialization ON doctors(specialization);
CREATE INDEX IF NOT EXISTS idx_staff_user_id ON staff(user_id);

-- Appointments Queue & Filtering
CREATE INDEX IF NOT EXISTS idx_appointments_patient_id ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor_id ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date_status ON appointments(preferred_date, status);

-- Medical Assessments
CREATE INDEX IF NOT EXISTS idx_assessments_patient_id ON medical_assessments(patient_id);
CREATE INDEX IF NOT EXISTS idx_assessments_created ON medical_assessments(created_at);

-- Laboratory Workflow
CREATE INDEX IF NOT EXISTS idx_lab_tests_patient_id ON laboratory_tests(patient_id);
CREATE INDEX IF NOT EXISTS idx_lab_tests_staff_id ON laboratory_tests(staff_id);
CREATE INDEX IF NOT EXISTS idx_lab_tests_status ON laboratory_tests(status);
CREATE INDEX IF NOT EXISTS idx_lab_results_test_id ON laboratory_results(test_id);

-- Predictions & Clinical Notes
CREATE INDEX IF NOT EXISTS idx_predictions_patient_id ON prediction_records(patient_id);
CREATE INDEX IF NOT EXISTS idx_predictions_doctor_id ON prediction_records(doctor_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON prediction_records(created_at);
CREATE INDEX IF NOT EXISTS idx_clinical_notes_patient ON clinical_notes(patient_id);

-- Notifications & Audit Logs
CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource, action);
