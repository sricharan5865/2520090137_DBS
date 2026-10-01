-- ====================================================================
-- STORED PROCEDURES & FUNCTIONS (DBMS Advanced Features)
-- ====================================================================

-- 1. Function: Atomic Appointment Booking with Double-Booking Prevention
CREATE OR REPLACE FUNCTION sp_book_appointment(
    p_patient_id VARCHAR(50),
    p_doctor_id VARCHAR(50),
    p_department VARCHAR(100),
    p_preferred_date DATE,
    p_preferred_time VARCHAR(20),
    p_reason TEXT
) RETURNS INTEGER AS $$
DECLARE
    v_existing_count INTEGER;
    v_new_appointment_id INTEGER;
    v_patient_user_id INTEGER;
    v_doctor_user_id INTEGER;
BEGIN
    -- Check if doctor is already booked for the exact time slot
    SELECT COUNT(*) INTO v_existing_count
    FROM appointments
    WHERE doctor_id = p_doctor_id
      AND preferred_date = p_preferred_date
      AND preferred_time = p_preferred_time
      AND status NOT IN ('Cancelled');

    IF v_existing_count > 0 THEN
        RAISE EXCEPTION 'Doctor % is already booked for date % at %', p_doctor_id, p_preferred_date, p_preferred_time;
    END IF;

    -- Insert appointment record
    INSERT INTO appointments (
        patient_id, doctor_id, department, preferred_date, preferred_time, reason_for_visit, status
    ) VALUES (
        p_patient_id, p_doctor_id, p_department, p_preferred_date, p_preferred_time, p_reason, 'Requested'
    ) RETURNING appointment_id INTO v_new_appointment_id;

    -- Auto-create doctor patient assignment if not already existing
    INSERT INTO doctor_patient_assignments (patient_id, doctor_id)
    VALUES (p_patient_id, p_doctor_id)
    ON CONFLICT (patient_id, doctor_id) DO NOTHING;

    -- Generate notification for the doctor
    SELECT user_id INTO v_doctor_user_id FROM doctors WHERE doctor_id = p_doctor_id;
    IF v_doctor_user_id IS NOT NULL THEN
        INSERT INTO notifications (recipient_user_id, title, message, category, link_url)
        VALUES (
            v_doctor_user_id,
            'New Appointment Requested',
            'Patient ' || p_patient_id || ' requested an appointment on ' || p_preferred_date || ' at ' || p_preferred_time,
            'Appointment',
            '/doctor/index.html'
        );
    END IF;

    RETURN v_new_appointment_id;
END;
$$ LANGUAGE plpgsql;


-- 2. Function: Verify Laboratory Test and Notify Doctor & Patient
CREATE OR REPLACE FUNCTION sp_verify_lab_test(
    p_test_id INTEGER,
    p_staff_id VARCHAR(50),
    p_comments TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    v_patient_id VARCHAR(50);
    v_doctor_id VARCHAR(50);
    v_patient_user_id INTEGER;
    v_doctor_user_id INTEGER;
    v_test_name VARCHAR(150);
BEGIN
    -- Update test status to Verified
    UPDATE laboratory_tests
    SET status = 'Verified',
        staff_id = p_staff_id,
        comments = COALESCE(p_comments, comments),
        updated_at = CURRENT_TIMESTAMP
    WHERE test_id = p_test_id
    RETURNING patient_id, doctor_id, test_name INTO v_patient_id, v_doctor_id, v_test_name;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Laboratory test ID % not found', p_test_id;
    END IF;

    -- Notify Patient
    SELECT user_id INTO v_patient_user_id FROM patients WHERE patient_id = v_patient_id;
    IF v_patient_user_id IS NOT NULL THEN
        INSERT INTO notifications (recipient_user_id, title, message, category, link_url)
        VALUES (
            v_patient_user_id,
            'Laboratory Report Verified',
            'Your lab report for ' || v_test_name || ' has been verified and is ready for review.',
            'Laboratory',
            '/patient/index.html'
        );
    END IF;

    -- Notify Doctor if assigned
    IF v_doctor_id IS NOT NULL THEN
        SELECT user_id INTO v_doctor_user_id FROM doctors WHERE doctor_id = v_doctor_id;
        IF v_doctor_user_id IS NOT NULL THEN
            INSERT INTO notifications (recipient_user_id, title, message, category, link_url)
            VALUES (
                v_doctor_user_id,
                'Lab Results Ready for Patient',
                'Verified lab results available for Patient ' || v_patient_id || ' (' || v_test_name || ')',
                'Laboratory',
                '/doctor/index.html'
            );
        END IF;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
