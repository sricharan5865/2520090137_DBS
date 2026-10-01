-- ====================================================================
-- SMART CHRONIC KIDNEY DISEASE RISK PREDICTION & PATIENT MANAGEMENT
-- DATABASE SCHEMA DEFINITION (PostgreSQL / ANSI SQL Compatible)
-- ====================================================================

-- Enable UUID extension if available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- --------------------------------------------------------------------
-- 1. ROLES TABLE (RBAC)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE CHECK (role_name IN ('ADMIN', 'DOCTOR', 'STAFF', 'PATIENT')),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 2. USERS TABLE (Authentication & Core Identity)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_name VARCHAR(50) NOT NULL REFERENCES roles(role_name) ON UPDATE CASCADE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 3. PATIENTS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    emergency_contact VARCHAR(100) NOT NULL,
    blood_group VARCHAR(10) NOT NULL CHECK (blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 4. DOCTORS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    specialization VARCHAR(100) NOT NULL DEFAULT 'Nephrology',
    department VARCHAR(100) NOT NULL DEFAULT 'Renal Medicine',
    license_number VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(255) NOT NULL,
    consulting_hours VARCHAR(100) DEFAULT '09:00 AM - 05:00 PM',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 5. STAFF TABLE (Laboratory / Clinical Staff)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staff (
    staff_id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL DEFAULT 'Clinical Pathology',
    designation VARCHAR(100) NOT NULL DEFAULT 'Lab Technologist',
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 6. DOCTOR-PATIENT ASSIGNMENTS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctor_patient_assignments (
    assignment_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id VARCHAR(50) NOT NULL REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    assigned_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Active' CHECK (status IN ('Active', 'Discharged', 'Transferred')),
    UNIQUE (patient_id, doctor_id)
);

-- --------------------------------------------------------------------
-- 7. APPOINTMENTS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id VARCHAR(50) NOT NULL REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    department VARCHAR(100) NOT NULL DEFAULT 'Nephrology',
    preferred_date DATE NOT NULL,
    preferred_time VARCHAR(20) NOT NULL,
    reason_for_visit TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Requested' CHECK (status IN ('Requested', 'Confirmed', 'Rescheduled', 'Completed', 'Cancelled')),
    cancellation_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Prevent exact duplicate double bookings for the same doctor and time slot on active appointments
    CONSTRAINT unique_doctor_slot UNIQUE (doctor_id, preferred_date, preferred_time)
);

-- --------------------------------------------------------------------
-- 8. PATIENT MEDICAL ASSESSMENTS TABLE (All 24 UCI CKD Clinical Features)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS medical_assessments (
    assessment_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    -- Clinical Numerics
    age NUMERIC(5, 1) CHECK (age >= 0 AND age <= 130),
    bp NUMERIC(5, 1) CHECK (bp >= 30 AND bp <= 260),
    sg NUMERIC(5, 3) CHECK (sg IN (1.005, 1.010, 1.015, 1.020, 1.025)),
    al NUMERIC(3, 1) CHECK (al >= 0 AND al <= 5),
    su NUMERIC(3, 1) CHECK (su >= 0 AND su <= 5),
    bgr NUMERIC(6, 1) CHECK (bgr >= 20 AND bgr <= 600),
    bu NUMERIC(6, 1) CHECK (bu >= 1 AND bu <= 400),
    sc NUMERIC(6, 2) CHECK (sc >= 0.1 AND sc <= 50.0),
    sod NUMERIC(6, 1) CHECK (sod >= 50 AND sod <= 200),
    pot NUMERIC(6, 2) CHECK (pot >= 1.0 AND pot <= 15.0),
    hemo NUMERIC(5, 2) CHECK (hemo >= 2.0 AND hemo <= 25.0),
    pcv NUMERIC(5, 1) CHECK (pcv >= 10 AND pcv <= 70),
    wc NUMERIC(8, 1) CHECK (wc >= 1000 AND wc <= 50000),
    rc NUMERIC(5, 2) CHECK (rc >= 1.0 AND rc <= 10.0),
    -- Clinical Categoricals
    rbc VARCHAR(20) CHECK (rbc IN ('normal', 'abnormal')),
    pc VARCHAR(20) CHECK (pc IN ('normal', 'abnormal')),
    pcc VARCHAR(20) CHECK (pcc IN ('present', 'notpresent')),
    ba VARCHAR(20) CHECK (ba IN ('present', 'notpresent')),
    htn VARCHAR(10) CHECK (htn IN ('yes', 'no')),
    dm VARCHAR(10) CHECK (dm IN ('yes', 'no')),
    cad VARCHAR(10) CHECK (cad IN ('yes', 'no')),
    appet VARCHAR(20) CHECK (appet IN ('good', 'poor')),
    pe VARCHAR(10) CHECK (pe IN ('yes', 'no')),
    ane VARCHAR(10) CHECK (ane IN ('yes', 'no')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 9. LABORATORY TESTS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS laboratory_tests (
    test_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    staff_id VARCHAR(50) REFERENCES staff(staff_id) ON DELETE SET NULL,
    doctor_id VARCHAR(50) REFERENCES doctors(doctor_id) ON DELETE SET NULL,
    test_name VARCHAR(150) NOT NULL,
    sample_type VARCHAR(100) DEFAULT 'Blood & Urine',
    test_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'Requested' CHECK (status IN ('Requested', 'Sample Collected', 'Processing', 'Completed', 'Verified')),
    report_file_url VARCHAR(500),
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 10. LABORATORY RESULTS TABLE (Structured Biomarker Values)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS laboratory_results (
    result_id SERIAL PRIMARY KEY,
    test_id INTEGER NOT NULL REFERENCES laboratory_tests(test_id) ON DELETE CASCADE,
    parameter_name VARCHAR(100) NOT NULL,
    parameter_code VARCHAR(20) NOT NULL,
    test_value NUMERIC(10, 3) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    reference_range VARCHAR(100) NOT NULL,
    abnormal_status VARCHAR(20) NOT NULL CHECK (abnormal_status IN ('Normal', 'High', 'Low', 'Abnormal')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 11. PREDICTION RECORDS TABLE (ML Output & Decision Support Logs)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prediction_records (
    prediction_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id VARCHAR(50) REFERENCES doctors(doctor_id) ON DELETE SET NULL,
    assessment_id INTEGER REFERENCES medical_assessments(assessment_id) ON DELETE SET NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    prediction_result VARCHAR(50) NOT NULL CHECK (prediction_result IN ('CKD Detected', 'No CKD Detected')),
    probability NUMERIC(5, 4) NOT NULL,
    risk_level VARCHAR(30) NOT NULL CHECK (risk_level IN ('Low Risk', 'Moderate Risk', 'High Risk', 'Critical Risk')),
    top_factors_json JSONB,
    shap_explanation_json JSONB,
    clinical_disclaimer TEXT NOT NULL DEFAULT 'ML prediction is intended for decision support and should be interpreted by a qualified healthcare professional.',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 12. CLINICAL NOTES & RECOMMENDATIONS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clinical_notes (
    note_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id VARCHAR(50) NOT NULL REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    appointment_id INTEGER REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    prediction_id INTEGER REFERENCES prediction_records(prediction_id) ON DELETE SET NULL,
    clinical_summary TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    treatment_plan TEXT NOT NULL,
    prescriptions TEXT,
    follow_up_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 13. NOTIFICATIONS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    recipient_user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('Appointment', 'Laboratory', 'Prediction', 'System', 'Clinical')),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    link_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------------------
-- 14. AUDIT LOGS TABLE
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    role_name VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100),
    details JSONB,
    ip_address VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
