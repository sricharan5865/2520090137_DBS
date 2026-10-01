import os
import sys
import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.config import settings
from backend.app.database.session import engine, Base, SessionLocal
from backend.app.models.entities import Role, User, Patient, Doctor, Staff, MedicalAssessment, Appointment, LaboratoryTest, LaboratoryResult, PredictionRecord, ClinicalNote, Notification
from backend.app.core.security import get_password_hash
from backend.app.routes import (
    auth, patients, doctors, staff, appointments, laboratory, predictions, admin, notifications
)

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Integrated Machine Learning + Database Management System for CKD Risk Prediction & Hospital Management",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware (Configurable for deployed frontend domains)
cors_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Include API Routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(patients.router, prefix=settings.API_PREFIX)
app.include_router(doctors.router, prefix=settings.API_PREFIX)
app.include_router(staff.router, prefix=settings.API_PREFIX)
app.include_router(appointments.router, prefix=settings.API_PREFIX)
app.include_router(laboratory.router, prefix=settings.API_PREFIX)
app.include_router(predictions.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)
app.include_router(notifications.router, prefix=settings.API_PREFIX)

# Ensure upload directory exists and mount static uploads
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Frontend directory mounting
frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
if os.path.exists(frontend_dir):
    assets_dir = os.path.join(frontend_dir, "assets")
    css_dir = os.path.join(frontend_dir, "css")
    js_dir = os.path.join(frontend_dir, "js")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.on_event("startup")
def startup_event():
    """Initializes database tables and default seed accounts."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed Roles
        roles = [
            ("ADMIN", "System Administrator with full management & analytics access"),
            ("DOCTOR", "Licensed Medical Practitioner / Nephrologist"),
            ("STAFF", "Clinical Laboratory Technologist & Healthcare Staff"),
            ("PATIENT", "Registered Patient seeking medical review and lab analysis")
        ]
        for r_name, r_desc in roles:
            if not db.query(Role).filter(Role.role_name == r_name).first():
                db.add(Role(role_name=r_name, description=r_desc))
        db.commit()

        # 2. Seed Default Admin User if not existing
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@hospital.com",
                password_hash=get_password_hash("Admin@123"),
                role_name="ADMIN",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("[Database] Seeded default Admin: admin@hospital.com / Admin@123")

        # 3. Seed Default Doctor if not existing
        doc_user = db.query(User).filter(User.username == "dr_sarah").first()
        if not doc_user:
            doc_user = User(
                username="dr_sarah",
                email="doctor.sarah@hospital.com",
                password_hash=get_password_hash("Doctor@123"),
                role_name="DOCTOR",
                is_active=True
            )
            db.add(doc_user)
            db.flush()
            doctor_profile = Doctor(
                doctor_id="DOC-101",
                user_id=doc_user.user_id,
                full_name="Dr. Sarah Jenkins, MD",
                specialization="Chief Nephrologist",
                department="Department of Renal Medicine",
                license_number="MED-LIC-88291",
                phone="+1 (555) 234-5678",
                email="doctor.sarah@hospital.com"
            )
            db.add(doctor_profile)
            db.commit()
            print("[Database] Seeded default Doctor: doctor.sarah@hospital.com / Doctor@123")

        # 4. Seed Default Staff if not existing
        stf_user = db.query(User).filter(User.username == "staff_james").first()
        if not stf_user:
            stf_user = User(
                username="staff_james",
                email="staff.james@hospital.com",
                password_hash=get_password_hash("Staff@123"),
                role_name="STAFF",
                is_active=True
            )
            db.add(stf_user)
            db.flush()
            staff_profile = Staff(
                staff_id="STF-501",
                user_id=stf_user.user_id,
                full_name="James Wilson, MLS",
                department="Central Diagnostic Laboratory",
                designation="Senior Clinical Pathology Technologist",
                phone="+1 (555) 456-7890",
                email="staff.james@hospital.com"
            )
            db.add(staff_profile)
            db.commit()
            print("[Database] Seeded default Staff: staff.james@hospital.com / Staff@123")

        # 5. Seed Default Patient if not existing
        pat_user = db.query(User).filter(User.username == "patient_john").first()
        if not pat_user:
            pat_user = User(
                username="patient_john",
                email="patient.john@hospital.com",
                password_hash=get_password_hash("Patient@123"),
                role_name="PATIENT",
                is_active=True
            )
            db.add(pat_user)
            db.flush()
            patient_profile = Patient(
                patient_id="PAT-001",
                user_id=pat_user.user_id,
                full_name="Johnathan Miller",
                date_of_birth=datetime.date(1968, 5, 14),
                gender="Male",
                phone="+1 (555) 678-1234",
                email="patient.john@hospital.com",
                address="742 Evergreen Terrace, Springfield",
                emergency_contact="+1 (555) 999-1122 (Wife)",
                blood_group="O+"
            )
            db.add(patient_profile)
            db.commit()

            # Seed Assessment for John
            assessment = MedicalAssessment(
                patient_id="PAT-001",
                age=58.0, bp=90.0, sg=1.010, al=3.0, su=1.0,
                rbc="abnormal", pc="abnormal", pcc="present", ba="notpresent",
                bgr=160.0, bu=68.0, sc=3.4, sod=131.0, pot=5.2,
                hemo=9.4, pcv=29.0, wc=9800.0, rc=3.5,
                htn="yes", dm="yes", cad="no", appet="poor", pe="yes", ane="yes",
                notes="Patient presents with elevated blood urea, creatinine, and chronic hypertension."
            )
            db.add(assessment)
            db.flush()

            # Seed Appointment
            appointment = Appointment(
                patient_id="PAT-001",
                doctor_id="DOC-101",
                department="Nephrology",
                preferred_date=datetime.date.today() + datetime.timedelta(days=1),
                preferred_time="10:00 AM",
                reason_for_visit="Follow-up on elevated serum creatinine and edema evaluation",
                status="Confirmed"
            )
            db.add(appointment)
            db.flush()

            # Seed Lab Test & Results
            lab_test = LaboratoryTest(
                patient_id="PAT-001",
                staff_id="STF-501",
                doctor_id="DOC-101",
                test_name="Comprehensive Renal Function Panel (RFP)",
                sample_type="Serum & 24hr Urine",
                status="Verified",
                comments="Marked elevation in BUN and serum creatinine. Moderate proteinuria noted."
            )
            db.add(lab_test)
            db.flush()

            results_data = [
                ("Serum Creatinine", "SC", 3.40, "mg/dL", "0.6 - 1.2", "High"),
                ("Blood Urea Nitrogen", "BU", 68.0, "mg/dL", "7 - 20", "High"),
                ("Urine Specific Gravity", "SG", 1.010, "", "1.015 - 1.025", "Low"),
                ("Hemoglobin", "HEMO", 9.4, "g/dL", "13.5 - 17.5", "Low"),
                ("Serum Potassium", "POT", 5.2, "mEq/L", "3.5 - 5.0", "High"),
                ("Serum Sodium", "SOD", 131.0, "mEq/L", "135 - 145", "Low")
            ]
            for p_name, p_code, val, unit, ref, abn in results_data:
                db.add(LaboratoryResult(
                    test_id=lab_test.test_id,
                    parameter_name=p_name,
                    parameter_code=p_code,
                    test_value=val,
                    unit=unit,
                    reference_range=ref,
                    abnormal_status=abn
                ))

            # Seed Prediction Record
            pred_record = PredictionRecord(
                patient_id="PAT-001",
                doctor_id="DOC-101",
                assessment_id=assessment.assessment_id,
                model_name="XGBoost",
                model_version="1.0.0",
                prediction_result="CKD Detected",
                probability=0.9840,
                risk_level="High Risk",
                top_factors_json=[
                    {"feature": "hemo", "friendly_name": "Hemoglobin Level", "shap_value": 1.43, "risk_impact": "Increases CKD Risk"},
                    {"feature": "sc", "friendly_name": "Serum Creatinine", "shap_value": 0.92, "risk_impact": "Increases CKD Risk"},
                    {"feature": "al", "friendly_name": "Albuminuria", "shap_value": 0.90, "risk_impact": "Increases CKD Risk"}
                ],
                shap_explanation_json={"base_value": -0.42, "model": "XGBoost Classifier v1.0.0"}
            )
            db.add(pred_record)
            db.commit()
            print("[Database] Seeded default Patient Johnathan Miller (PAT-001) with full clinical records.")
    except Exception as e:
        print(f"[Database Startup Error]: {e}")
        db.rollback()
    finally:
        db.close()

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected"
    }

# Serve root landing and portal pages directly
@app.get("/")
def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": f"Welcome to {settings.PROJECT_NAME} API. Visit /docs for OpenAPI documentation."}

@app.get("/login.html")
def serve_login():
    return FileResponse(os.path.join(frontend_dir, "login.html"))

@app.get("/register.html")
def serve_register():
    return FileResponse(os.path.join(frontend_dir, "register.html"))

@app.get("/patient/index.html")
def serve_patient_portal():
    return FileResponse(os.path.join(frontend_dir, "patient", "index.html"))

@app.get("/doctor/index.html")
def serve_doctor_portal():
    return FileResponse(os.path.join(frontend_dir, "doctor", "index.html"))

@app.get("/staff/index.html")
def serve_staff_portal():
    return FileResponse(os.path.join(frontend_dir, "staff", "index.html"))

@app.get("/admin/index.html")
def serve_admin_portal():
    return FileResponse(os.path.join(frontend_dir, "admin", "index.html"))
