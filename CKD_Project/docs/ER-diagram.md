# Entity-Relationship (ER) Diagram & Relational Schema Documentation

## 1. System ER Diagram (Mermaid)

```mermaid
erDiagram
    ROLES ||--o{ USERS : "assigned_to"
    USERS ||--o| PATIENTS : "identifies"
    USERS ||--o| DOCTORS : "identifies"
    USERS ||--o| STAFF : "identifies"
    USERS ||--o{ NOTIFICATIONS : "receives"
    USERS ||--o{ AUDIT_LOGS : "triggers"

    PATIENTS ||--o{ APPOINTMENTS : "books"
    DOCTORS ||--o{ APPOINTMENTS : "conducts"
    
    PATIENTS ||--o{ MEDICAL_ASSESSMENTS : "submits"
    PATIENTS ||--o{ LABORATORY_TESTS : "undergoes"
    STAFF ||--o{ LABORATORY_TESTS : "processes"
    DOCTORS ||--o{ LABORATORY_TESTS : "orders"
    LABORATORY_TESTS ||--|{ LABORATORY_RESULTS : "contains"

    PATIENTS ||--o{ PREDICTION_RECORDS : "evaluates"
    DOCTORS ||--o{ PREDICTION_RECORDS : "reviews"
    MEDICAL_ASSESSMENTS ||--o| PREDICTION_RECORDS : "inputs_into"

    PATIENTS ||--o{ CLINICAL_NOTES : "receives"
    DOCTORS ||--o{ CLINICAL_NOTES : "writes"
    APPOINTMENTS ||--o| CLINICAL_NOTES : "documents"
    PREDICTION_RECORDS ||--o| CLINICAL_NOTES : "references"

    PATIENTS ||--o{ DOCTOR_PATIENT_ASSIGNMENTS : "assigned_to"
    DOCTORS ||--o{ DOCTOR_PATIENT_ASSIGNMENTS : "responsible_for"

    ROLES {
        int role_id PK
        string role_name UK "ADMIN, DOCTOR, STAFF, PATIENT"
        string description
        timestamp created_at
    }

    USERS {
        int user_id PK
        string username UK
        string email UK
        string password_hash
        string role_name FK
        boolean is_active
        timestamp last_login
        timestamp created_at
    }

    PATIENTS {
        string patient_id PK "e.g. PAT-001"
        int user_id FK, UK
        string full_name
        date date_of_birth
        string gender "Male, Female, Other"
        string phone
        string email
        text address
        string emergency_contact
        string blood_group "O+, A+, B+, AB+, etc."
    }

    DOCTORS {
        string doctor_id PK "e.g. DOC-101"
        int user_id FK, UK
        string full_name
        string specialization
        string department
        string license_number UK
        string phone
        string email
        string consulting_hours
    }

    STAFF {
        string staff_id PK "e.g. STF-501"
        int user_id FK, UK
        string full_name
        string department
        string designation
        string phone
        string email
    }

    APPOINTMENTS {
        int appointment_id PK
        string patient_id FK
        string doctor_id FK
        string department
        date preferred_date
        string preferred_time
        text reason_for_visit
        string status "Requested, Confirmed, Completed, Cancelled"
        text cancellation_reason
    }

    MEDICAL_ASSESSMENTS {
        int assessment_id PK
        string patient_id FK
        numeric age
        numeric bp
        numeric sg
        numeric al
        numeric su
        numeric bgr
        numeric bu
        numeric sc
        numeric sod
        numeric pot
        numeric hemo
        numeric pcv
        numeric wc
        numeric rc
        string rbc
        string pc
        string pcc
        string ba
        string htn
        string dm
        string cad
        string appet
        string pe
        string ane
        text notes
    }

    LABORATORY_TESTS {
        int test_id PK
        string patient_id FK
        string staff_id FK
        string doctor_id FK
        string test_name
        string sample_type
        timestamp test_date
        string status "Requested, Processing, Completed, Verified"
        string report_file_url
        text comments
    }

    LABORATORY_RESULTS {
        int result_id PK
        int test_id FK
        string parameter_name
        string parameter_code
        numeric test_value
        string unit
        string reference_range
        string abnormal_status "Normal, High, Low, Abnormal"
    }

    PREDICTION_RECORDS {
        int prediction_id PK
        string patient_id FK
        string doctor_id FK
        int assessment_id FK
        string model_name "XGBoost, LightGBM"
        string model_version
        string prediction_result "CKD Detected, No CKD Detected"
        numeric probability
        string risk_level "Low Risk, Moderate Risk, High Risk, Critical Risk"
        jsonb top_factors_json
        jsonb shap_explanation_json
        text clinical_disclaimer
    }

    CLINICAL_NOTES {
        int note_id PK
        string patient_id FK
        string doctor_id FK
        int appointment_id FK
        int prediction_id FK
        text clinical_summary
        text diagnosis
        text treatment_plan
        text prescriptions
        date follow_up_date
    }
```

---

## 2. Normalization Analysis (Up to 3NF)

1. **First Normal Form (1NF)**:
   - All columns hold atomic, indivisible values.
   - Repeating groups (e.g. individual lab parameters like Creatinine, BUN, Potassium) are extracted into the dedicated child table `laboratory_results`.
   - Every table contains a well-defined Primary Key.

2. **Second Normal Form (2NF)**:
   - The schema satisfies 1NF.
   - No non-prime attribute is partially dependent on any composite primary key. Composite keys (e.g., `doctor_patient_assignments(patient_id, doctor_id)`) only establish associative identity.

3. **Third Normal Form (3NF)**:
   - The schema satisfies 2NF.
   - All non-key attributes are directly dependent **only** on the primary key, with no transitive functional dependencies (e.g., Doctor specialization is keyed under `doctors`, not redundantly stored across appointments).

---

## 3. Referential Integrity & Constraints
- **Primary Keys**: Assigned across all 14 entities.
- **Foreign Keys with Cascade Actions**:
  - `ON DELETE CASCADE` on patient child records (assessments, appointments, results).
  - `ON DELETE SET NULL` on technician/doctor audit references to preserve data provenance.
- **CHECK Constraints**: Numeric physiological bounds (e.g. `age BETWEEN 0 AND 130`, `bp BETWEEN 30 AND 260`), enum validations (`gender IN ('Male','Female','Other')`).
- **Unique Slot Constraints**: `UNIQUE(doctor_id, preferred_date, preferred_time)` prevents double-booking.
- **Database Views**:
  - `v_patient_360`: Real-time composite view of patient history, latest assessments, and predictions.
  - `v_doctor_workload`: Aggregated appointment and review metrics grouped per doctor.
  - `v_lab_queue`: Pending laboratory requests and abnormal count aggregations.
