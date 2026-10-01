import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, Numeric,
    ForeignKey, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_name = Column(String(50), ForeignKey("roles.role_name", onupdate="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    role = relationship("Role", back_populates="users")
    patient_profile = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor_profile = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    staff_profile = relationship("Staff", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="recipient", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String(50), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    emergency_contact = Column(String(100), nullable=False)
    blood_group = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="patient_profile")
    assessments = relationship("MedicalAssessment", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    laboratory_tests = relationship("LaboratoryTest", back_populates="patient", cascade="all, delete-orphan")
    prediction_records = relationship("PredictionRecord", back_populates="patient", cascade="all, delete-orphan")
    clinical_notes = relationship("ClinicalNote", back_populates="patient", cascade="all, delete-orphan")
    doctor_assignments = relationship("DoctorPatientAssignment", back_populates="patient", cascade="all, delete-orphan")


class Doctor(Base):
    __tablename__ = "doctors"

    doctor_id = Column(String(50), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    specialization = Column(String(100), default="Nephrology", nullable=False)
    department = Column(String(100), default="Renal Medicine", nullable=False)
    license_number = Column(String(100), unique=True, nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(255), nullable=False)
    consulting_hours = Column(String(100), default="09:00 AM - 05:00 PM")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="doctor_profile")
    appointments = relationship("Appointment", back_populates="doctor")
    patient_assignments = relationship("DoctorPatientAssignment", back_populates="doctor")
    clinical_notes = relationship("ClinicalNote", back_populates="doctor")
    reviewed_predictions = relationship("PredictionRecord", back_populates="doctor")


class Staff(Base):
    __tablename__ = "staff"

    staff_id = Column(String(50), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    department = Column(String(100), default="Clinical Pathology", nullable=False)
    designation = Column(String(100), default="Lab Technologist", nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="staff_profile")
    processed_lab_tests = relationship("LaboratoryTest", back_populates="staff")


class DoctorPatientAssignment(Base):
    __tablename__ = "doctor_patient_assignments"

    assignment_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(String(50), ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False)
    assigned_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="Active")

    __table_args__ = (UniqueConstraint("patient_id", "doctor_id", name="uq_patient_doctor"),)

    patient = relationship("Patient", back_populates="doctor_assignments")
    doctor = relationship("Doctor", back_populates="patient_assignments")


class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(String(50), ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False)
    department = Column(String(100), default="Nephrology", nullable=False)
    preferred_date = Column(Date, nullable=False)
    preferred_time = Column(String(20), nullable=False)
    reason_for_visit = Column(Text, nullable=False)
    status = Column(String(50), default="Requested", nullable=False)
    cancellation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (UniqueConstraint("doctor_id", "preferred_date", "preferred_time", name="uq_doctor_slot"),)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    clinical_note = relationship("ClinicalNote", back_populates="appointment", uselist=False)


class MedicalAssessment(Base):
    __tablename__ = "medical_assessments"

    assessment_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    
    # 14 Numeric features
    age = Column(Numeric(5, 1), nullable=True)
    bp = Column(Numeric(5, 1), nullable=True)
    sg = Column(Numeric(5, 3), nullable=True)
    al = Column(Numeric(3, 1), nullable=True)
    su = Column(Numeric(3, 1), nullable=True)
    bgr = Column(Numeric(6, 1), nullable=True)
    bu = Column(Numeric(6, 1), nullable=True)
    sc = Column(Numeric(6, 2), nullable=True)
    sod = Column(Numeric(6, 1), nullable=True)
    pot = Column(Numeric(6, 2), nullable=True)
    hemo = Column(Numeric(5, 2), nullable=True)
    pcv = Column(Numeric(5, 1), nullable=True)
    wc = Column(Numeric(8, 1), nullable=True)
    rc = Column(Numeric(5, 2), nullable=True)
    
    # 10 Categorical features
    rbc = Column(String(20), nullable=True)
    pc = Column(String(20), nullable=True)
    pcc = Column(String(20), nullable=True)
    ba = Column(String(20), nullable=True)
    htn = Column(String(10), nullable=True)
    dm = Column(String(10), nullable=True)
    cad = Column(String(10), nullable=True)
    appet = Column(String(20), nullable=True)
    pe = Column(String(10), nullable=True)
    ane = Column(String(10), nullable=True)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="assessments")
    prediction_records = relationship("PredictionRecord", back_populates="assessment")


class LaboratoryTest(Base):
    __tablename__ = "laboratory_tests"

    test_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    staff_id = Column(String(50), ForeignKey("staff.staff_id", ondelete="SET NULL"), nullable=True)
    doctor_id = Column(String(50), ForeignKey("doctors.doctor_id", ondelete="SET NULL"), nullable=True)
    test_name = Column(String(150), nullable=False)
    sample_type = Column(String(100), default="Blood & Urine")
    test_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="Requested", nullable=False)
    report_file_url = Column(String(500), nullable=True)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="laboratory_tests")
    staff = relationship("Staff", back_populates="processed_lab_tests")
    doctor = relationship("Doctor")
    results = relationship("LaboratoryResult", back_populates="test", cascade="all, delete-orphan")


class LaboratoryResult(Base):
    __tablename__ = "laboratory_results"

    result_id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("laboratory_tests.test_id", ondelete="CASCADE"), nullable=False)
    parameter_name = Column(String(100), nullable=False)
    parameter_code = Column(String(20), nullable=False)
    test_value = Column(Numeric(10, 3), nullable=False)
    unit = Column(String(50), nullable=False)
    reference_range = Column(String(100), nullable=False)
    abnormal_status = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    test = relationship("LaboratoryTest", back_populates="results")


class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    prediction_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(String(50), ForeignKey("doctors.doctor_id", ondelete="SET NULL"), nullable=True)
    assessment_id = Column(Integer, ForeignKey("medical_assessments.assessment_id", ondelete="SET NULL"), nullable=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    prediction_result = Column(String(50), nullable=False)
    probability = Column(Numeric(5, 4), nullable=False)
    risk_level = Column(String(30), nullable=False)
    top_factors_json = Column(JSON, nullable=True)
    shap_explanation_json = Column(JSON, nullable=True)
    clinical_disclaimer = Column(
        Text,
        default="ML prediction is intended for decision support and should be interpreted by a qualified healthcare professional.",
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="prediction_records")
    doctor = relationship("Doctor", back_populates="reviewed_predictions")
    assessment = relationship("MedicalAssessment", back_populates="prediction_records")
    clinical_notes = relationship("ClinicalNote", back_populates="prediction")


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    note_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(String(50), ForeignKey("doctors.doctor_id", ondelete="CASCADE"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.appointment_id", ondelete="SET NULL"), nullable=True)
    prediction_id = Column(Integer, ForeignKey("prediction_records.prediction_id", ondelete="SET NULL"), nullable=True)
    clinical_summary = Column(Text, nullable=False)
    diagnosis = Column(Text, nullable=False)
    treatment_plan = Column(Text, nullable=False)
    prescriptions = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="clinical_notes")
    doctor = relationship("Doctor", back_populates="clinical_notes")
    appointment = relationship("Appointment", back_populates="clinical_note")
    prediction = relationship("PredictionRecord", back_populates="clinical_notes")


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    recipient_user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), default="System", nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    link_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    recipient = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    role_name = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    status = Column(String(20), default="SUCCESS", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
