# Smart Chronic Kidney Disease (CKD) Risk Prediction & Patient Management System

An enterprise-grade, integrated **Machine Learning + Database Management System (DBMS)** healthcare web platform designed for clinical decision support, renal disease risk assessment, laboratory workflow automation, and multi-role hospital management.

---

## 🌟 Key Highlights & Academic Objectives

- **Genuine Machine Learning (Zero Data Leakage)**: Built and trained exclusively on the official **UCI Chronic Kidney Disease Benchmark Dataset** (400 instances, 24 clinical features + class label). Implements **XGBoost Classifier** and **LightGBM Classifier** with empirical metric evaluation and **SHAP (SHapley Additive exPlanations)** TreeExplainer.
- **Relational PostgreSQL DBMS**: 3NF-normalized relational schema featuring Primary & Foreign Keys, CHECK constraints, composite UNIQUE slots preventing appointment double-booking, B-tree indexes, PostgreSQL Views, Stored Functions/Procedures, Triggers, and an interactive SQL Query Runner for academic grading demonstration.
- **Role-Based Access Control (RBAC)**: Four distinct, isolated portals with JWT authentication and bcrypt encryption:
  1. **Admin**: System health metrics, user and role administration, prediction distribution charts, audit log tracing, and live SQL query execution.
  2. **Doctor**: Consultation queue, Patient 360 View, one-click ML prediction execution with SHAP feature contribution charts, clinical notes editor, and follow-up management.
  3. **Staff / Laboratory**: Pending requisition queue, biomarker parameter entry, diagnostic report file upload (PDF/images), and verification gating.
  4. **Patient**: Personal profile, 24-feature clinical assessment intake form, appointment booking, verified lab report access, and decision-support prediction review.
- **Medical Safety Standard**: Strict medical decision-support disclaimers ensuring machine learning outputs assist rather than replace clinical judgment.

---

## 📊 Dataset & Machine Learning Performance

### 1. Dataset Features (24 Clinical Attributes)
| Category | Features |
| :--- | :--- |
| **Numerical Biomarkers (14)** | `age`, `bp` (Blood Pressure), `sg` (Specific Gravity), `al` (Albumin), `su` (Sugar), `bgr` (Blood Glucose Random), `bu` (Blood Urea), `sc` (Serum Creatinine), `sod` (Sodium), `pot` (Potassium), `hemo` (Hemoglobin), `pcv` (Packed Cell Volume), `wc` (White Blood Cell Count), `rc` (Red Blood Cell Count) |
| **Categorical Symptoms (10)** | `rbc` (Red Blood Cells: normal/abnormal), `pc` (Pus Cell), `pcc` (Pus Cell Clumps), `ba` (Bacteria), `htn` (Hypertension), `dm` (Diabetes Mellitus), `cad` (Coronary Artery Disease), `appet` (Appetite: good/poor), `pe` (Pedal Edema), `ane` (Anemia) |
| **Target Label** | `classification` (`ckd`: Chronic Kidney Disease Detected, `notckd`: No CKD Detected) |

### 2. Empirical Model Comparison
The models were trained on 80% stratified train split and evaluated on the 20% test split:

| Evaluation Metric | XGBoost Classifier | LightGBM Classifier | Production Choice |
| :--- | :---: | :---: | :---: |
| **Accuracy** | **100.00%** | **100.00%** | `XGBoost v1.0.0` |
| **Precision** | **100.00%** | **100.00%** | `100.00%` |
| **Recall (Sensitivity)** | **100.00%** | **100.00%** | `100.00%` |
| **F1-Score** | **1.0000** | **1.0000** | `1.0000` |
| **ROC-AUC** | **1.0000** | **1.0000** | `1.0000` |

---

## 🗄️ Database Management System Features

The relational database architecture is defined under `database/`:
- `schema.sql`: Full DDL with 3NF normalization, table constraints, and foreign key cascades.
- `indexes.sql`: B-Tree indexes on user emails, patient IDs, appointment schedules, and test statuses.
- `views.sql`:
  - `v_patient_360`: Real-time composite view of patient history, latest assessments, and predictions.
  - `v_doctor_workload`: Aggregated appointment and review metrics grouped per doctor.
  - `v_lab_queue`: Pending laboratory requests and abnormal count aggregations.
  - `v_prediction_analytics`: Aggregated prediction distribution and model performance.
- `procedures.sql`:
  - `sp_book_appointment`: Atomic appointment booking with double-booking prevention.
  - `sp_verify_lab_test`: Atomic lab verification and multi-recipient notification generation.
- `triggers.sql`: Automated audit log triggers on user registration and prediction execution.
- `seed.sql`: Pre-populated clinical demonstration records.
- `demo_queries.sql`: 8 comprehensive demonstration queries for grading.

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- (Optional) PostgreSQL & Docker

### 1. Clone & Set Up Environment
```bash
git clone <repository_url>
cd CKD_Project

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Train the Machine Learning Pipeline
```bash
python ml/training/train.py
```
*Output: Trains XGBoost & LightGBM, calculates empirical test metrics, evaluates SHAP explainability, and saves `ml/models/best_model.joblib`.*

### 3. Run Automated Pytest Suite
```bash
python -m pytest tests/ -v
```
*Output: Runs 10 comprehensive unit & integration tests covering auth, RBAC, double-booking prevention, lab workflows, ML predictions, and DBMS queries.*

### 4. Start the Application Server
```bash
uvicorn backend.app.main:app --reload --port 8000
```

Open your browser and visit:
- **Web Platform**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔑 Default Demonstration Accounts

The database is seeded with ready-to-test accounts for all 4 roles:

| Role | Email / Username | Password | Dedicated Portal |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@hospital.com` | `Admin@123` | [Admin Portal](http://localhost:8000/admin/index.html) |
| **Doctor** | `doctor.sarah@hospital.com` | `Doctor@123` | [Doctor Portal](http://localhost:8000/doctor/index.html) |
| **Staff (Lab)** | `staff.james@hospital.com` | `Staff@123` | [Staff Portal](http://localhost:8000/staff/index.html) |
| **Patient** | `patient.john@hospital.com` | `Patient@123` | [Patient Portal](http://localhost:8000/patient/index.html) |

*(Quick 1-Click login buttons are available directly on the login page at [http://localhost:8000/login.html](http://localhost:8000/login.html))*

---

## 🎬 End-to-End Demonstration Scenario Walkthrough

Follow this 8-step sequence during project review or examination:

1. **Patient Intake & Assessment**:
   - Log in as **Patient John** (`patient.john@hospital.com` / `Patient@123`).
   - Navigate to **Medical Assessment** tab and submit patient vitals/symptoms.
   - Go to **Appointments** tab and book a consultation with Dr. Sarah.
2. **Laboratory Processing & Verification**:
   - Log in as **Staff James** (`staff.james@hospital.com` / `Staff@123`).
   - Open **Pending Lab Tests** to see the newly queued test requisition.
   - Click **Enter Results**, input serum creatinine (`3.4 mg/dL`), blood urea (`68 mg/dL`), etc.
   - Click **Save & Verify Report** to verify the panel and notify the doctor.
3. **Doctor Review & Explainable ML Inference**:
   - Log in as **Dr. Sarah** (`doctor.sarah@hospital.com` / `Doctor@123`).
   - Go to **Patient Search & 360**, search for `PAT-001` to view demographics, assessments, and verified lab values.
   - Click **Run CKD Prediction**, select **XGBoost Classifier**, and execute inference.
   - Inspect the **SHAP Feature Contribution bars** showing top risk drivers (Hemoglobin, Serum Creatinine, Albuminuria).
   - Click **Add Clinical Notes** to prescribe medication and schedule a follow-up.
4. **Patient Result Inspection**:
   - Log back into the **Patient Portal** to view the verified lab panel, doctor's prescription, and decision-support risk level.
5. **Admin Monitoring & Live SQL Evaluation**:
   - Log in as **Admin** (`admin@hospital.com` / `Admin@123`).
   - Review the real-time prediction distribution charts and system workload graphs.
   - Navigate to **SQL Query Runner (DBMS)** and click preset queries (e.g. Preset 1: JOIN query, Preset 5: Doctor Workload aggregation) to execute live on the database.
   - Review the **Audit Logs** for complete traceability.

---

## 🐳 Docker Deployment

To launch the complete multi-container stack with PostgreSQL, MongoDB, and FastAPI:
```bash
cd docker
docker-compose up --build -d
```
Service endpoints:
- Application: `http://localhost:8000`
- PostgreSQL: `localhost:5432` (User: `ckd_admin`, DB: `ckd_healthcare_db`)
- MongoDB: `localhost:27017`
