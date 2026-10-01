import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# ---------------------------------------------------------
# Authentication Schemas
# ---------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    user_id: int
    profile_id: Optional[str] = None
    full_name: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class PatientRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    date_of_birth: datetime.date
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    phone: str = Field(..., min_length=5)
    address: str = Field(..., min_length=3)
    emergency_contact: str = Field(..., min_length=2, max_length=100)
    blood_group: str = Field(..., pattern=r"^(A\+|A-|B\+|B-|AB\+|AB-|O\+|O-)$")

class DoctorCreateRequest(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    specialization: str = "Nephrology"
    department: str = "Renal Medicine"
    license_number: str
    phone: str
    consulting_hours: str = "09:00 AM - 05:00 PM"

class DoctorResponse(BaseModel):
    doctor_id: str
    full_name: str
    specialization: str
    department: str
    email: Optional[str] = None
    phone: Optional[str] = None
    consulting_hours: Optional[str] = None

    class Config:
        from_attributes = True

class StaffCreateRequest(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    department: str = "Clinical Pathology"
    designation: str = "Lab Technologist"
    phone: str

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role_name: str
    is_active: bool
    last_login: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# ---------------------------------------------------------
# Patient Schemas
# ---------------------------------------------------------
class PatientProfileResponse(BaseModel):
    patient_id: str
    user_id: int
    full_name: str
    date_of_birth: datetime.date
    gender: str
    phone: str
    email: str
    address: str
    emergency_contact: str
    blood_group: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class PatientProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None

# ---------------------------------------------------------
# Medical Assessment (All 24 UCI CKD Clinical Features)
# ---------------------------------------------------------
class MedicalAssessmentCreate(BaseModel):
    patient_id: Optional[str] = None
    # 14 Numeric features
    age: Optional[float] = Field(None, ge=1, le=120, description="Age in years")
    bp: Optional[float] = Field(None, ge=40, le=220, description="Blood Pressure in mm/Hg")
    sg: Optional[float] = Field(None, description="Urine Specific Gravity: 1.005, 1.010, 1.015, 1.020, 1.025")
    al: Optional[float] = Field(None, ge=0, le=5, description="Albumin (0 to 5)")
    su: Optional[float] = Field(None, ge=0, le=5, description="Sugar (0 to 5)")
    bgr: Optional[float] = Field(None, ge=20, le=600, description="Blood Glucose Random (mg/dL)")
    bu: Optional[float] = Field(None, ge=1, le=400, description="Blood Urea (mg/dL)")
    sc: Optional[float] = Field(None, ge=0.1, le=40.0, description="Serum Creatinine (mg/dL)")
    sod: Optional[float] = Field(None, ge=50, le=200, description="Sodium (mEq/L)")
    pot: Optional[float] = Field(None, ge=1.0, le=15.0, description="Potassium (mEq/L)")
    hemo: Optional[float] = Field(None, ge=2.0, le=25.0, description="Hemoglobin (g/dL)")
    pcv: Optional[float] = Field(None, ge=10, le=70, description="Packed Cell Volume (%)")
    wc: Optional[float] = Field(None, ge=1000, le=50000, description="White Blood Cell Count (/cu.mm)")
    rc: Optional[float] = Field(None, ge=1.0, le=10.0, description="Red Blood Cell Count (millions/cmm)")
    
    # 10 Categorical features
    rbc: Optional[str] = Field(None, pattern="^(normal|abnormal)$")
    pc: Optional[str] = Field(None, pattern="^(normal|abnormal)$")
    pcc: Optional[str] = Field(None, pattern="^(present|notpresent)$")
    ba: Optional[str] = Field(None, pattern="^(present|notpresent)$")
    htn: Optional[str] = Field(None, pattern="^(yes|no)$")
    dm: Optional[str] = Field(None, pattern="^(yes|no)$")
    cad: Optional[str] = Field(None, pattern="^(yes|no)$")
    appet: Optional[str] = Field(None, pattern="^(good|poor)$")
    pe: Optional[str] = Field(None, pattern="^(yes|no)$")
    ane: Optional[str] = Field(None, pattern="^(yes|no)$")
    notes: Optional[str] = None

class MedicalAssessmentResponse(MedicalAssessmentCreate):
    assessment_id: int
    patient_id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# ---------------------------------------------------------
# Appointment Schemas
# ---------------------------------------------------------
class AppointmentCreate(BaseModel):
    doctor_id: str
    department: str = "Nephrology"
    preferred_date: datetime.date
    preferred_time: str
    reason_for_visit: str = Field(..., min_length=3)

class AppointmentUpdateStatus(BaseModel):
    status: str = Field(..., pattern="^(Requested|Confirmed|Rescheduled|Completed|Cancelled)$")
    cancellation_reason: Optional[str] = None
    preferred_date: Optional[datetime.date] = None
    preferred_time: Optional[str] = None

class AppointmentResponse(BaseModel):
    appointment_id: int
    patient_id: str
    doctor_id: str
    department: str
    preferred_date: datetime.date
    preferred_time: str
    reason_for_visit: str
    status: str
    cancellation_reason: Optional[str] = None
    created_at: datetime.datetime
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None

    class Config:
        from_attributes = True

# ---------------------------------------------------------
# Laboratory Schemas
# ---------------------------------------------------------
class LaboratoryResultItem(BaseModel):
    parameter_name: str
    parameter_code: str
    test_value: float
    unit: str
    reference_range: str
    abnormal_status: str

class LaboratoryResultResponse(LaboratoryResultItem):
    result_id: int
    test_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class LaboratoryTestCreate(BaseModel):
    patient_id: str
    doctor_id: Optional[str] = None
    test_name: str
    sample_type: str = "Blood & Urine"
    comments: Optional[str] = None

class LaboratoryTestEnterResults(BaseModel):
    staff_id: Optional[str] = None
    results: List[LaboratoryResultItem]
    comments: Optional[str] = None
    status: str = "Completed"

class LaboratoryTestResponse(BaseModel):
    test_id: int
    patient_id: str
    staff_id: Optional[str] = None
    doctor_id: Optional[str] = None
    test_name: str
    sample_type: str
    test_date: datetime.datetime
    status: str
    report_file_url: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime.datetime
    patient_name: Optional[str] = None
    staff_name: Optional[str] = None
    doctor_name: Optional[str] = None
    results: List[LaboratoryResultResponse] = []

    class Config:
        from_attributes = True

# ---------------------------------------------------------
# Prediction & ML Schemas
# ---------------------------------------------------------
class PredictionRunRequest(BaseModel):
    patient_id: str
    doctor_id: Optional[str] = None
    assessment_id: Optional[int] = None
    model_choice: Optional[str] = "XGBoost"  # XGBoost or LightGBM
    override_features: Optional[Dict[str, Any]] = None

class PredictionResponse(BaseModel):
    prediction_id: int
    patient_id: str
    doctor_id: Optional[str] = None
    model_name: str
    model_version: str
    prediction_result: str
    probability: float
    risk_level: str
    top_factors: Optional[List[Dict[str, Any]]] = None
    shap_explanation: Optional[Dict[str, Any]] = None
    clinical_disclaimer: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# ---------------------------------------------------------
# Clinical Notes Schemas
# ---------------------------------------------------------
class ClinicalNoteCreate(BaseModel):
    patient_id: str
    appointment_id: Optional[int] = None
    prediction_id: Optional[int] = None
    clinical_summary: str = Field(..., min_length=5)
    diagnosis: str = Field(..., min_length=3)
    treatment_plan: str = Field(..., min_length=5)
    prescriptions: Optional[str] = None
    follow_up_date: Optional[datetime.date] = None

class ClinicalNoteResponse(BaseModel):
    note_id: int
    patient_id: str
    doctor_id: str
    appointment_id: Optional[int] = None
    prediction_id: Optional[int] = None
    clinical_summary: str
    diagnosis: str
    treatment_plan: str
    prescriptions: Optional[str] = None
    follow_up_date: Optional[datetime.date] = None
    created_at: datetime.datetime
    doctor_name: Optional[str] = None

    class Config:
        from_attributes = True

# ---------------------------------------------------------
# Notification & Audit Schemas
# ---------------------------------------------------------
class NotificationResponse(BaseModel):
    notification_id: int
    title: str
    message: str
    category: str
    is_read: bool
    link_url: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    log_id: int
    user_id: Optional[int] = None
    role_name: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
