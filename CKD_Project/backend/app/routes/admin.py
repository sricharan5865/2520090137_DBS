import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database.session import get_db
from backend.app.models.entities import (
    User, Role, Patient, Doctor, Staff, Appointment, LaboratoryTest, PredictionRecord, AuditLog
)
from backend.app.schemas.schemas import (
    DoctorCreateRequest, StaffCreateRequest, UserResponse, AuditLogResponse
)
from backend.app.auth.deps import require_role
from backend.app.core.security import get_password_hash
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/overview")
def get_admin_overview(
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    total_patients = db.query(Patient).count()
    total_doctors = db.query(Doctor).count()
    total_staff = db.query(Staff).count()
    total_appointments = db.query(Appointment).count()
    pending_appointments = db.query(Appointment).filter(Appointment.status == "Requested").count()
    completed_appointments = db.query(Appointment).filter(Appointment.status == "Completed").count()
    pending_lab_tests = db.query(LaboratoryTest).filter(LaboratoryTest.status.in_(["Requested", "Processing"])).count()
    completed_lab_tests = db.query(LaboratoryTest).filter(LaboratoryTest.status.in_(["Completed", "Verified"])).count()
    total_predictions = db.query(PredictionRecord).count()
    
    # Prediction distribution
    ckd_count = db.query(PredictionRecord).filter(PredictionRecord.prediction_result == "CKD Detected").count()
    not_ckd_count = db.query(PredictionRecord).filter(PredictionRecord.prediction_result == "No CKD Detected").count()
    
    # Recent users
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(6).all()
    # Recent audit logs
    recent_audits = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all()

    return {
        "metrics": {
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "total_staff": total_staff,
            "total_appointments": total_appointments,
            "pending_appointments": pending_appointments,
            "completed_appointments": completed_appointments,
            "pending_lab_tests": pending_lab_tests,
            "completed_lab_tests": completed_lab_tests,
            "total_predictions": total_predictions,
            "ckd_predictions": ckd_count,
            "not_ckd_predictions": not_ckd_count
        },
        "recent_users": [
            {
                "user_id": u.user_id,
                "username": u.username,
                "email": u.email,
                "role": u.role_name,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat()
            } for u in recent_users
        ],
        "recent_audits": [
            {
                "log_id": a.log_id,
                "action": a.action,
                "role": a.role_name,
                "resource": a.resource,
                "status": a.status,
                "timestamp": a.created_at.isoformat()
            } for a in recent_audits
        ]
    }

@router.get("/users")
def list_all_users(
    role_filter: Optional[str] = None,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if role_filter:
        query = query.filter(User.role_name == role_filter)
    users = query.order_by(User.created_at.desc()).all()
    
    res = []
    for u in users:
        name = u.username
        profile_id = "-"
        if u.role_name == "DOCTOR" and u.doctor_profile:
            name = u.doctor_profile.full_name
            profile_id = u.doctor_profile.doctor_id
        elif u.role_name == "STAFF" and u.staff_profile:
            name = u.staff_profile.full_name
            profile_id = u.staff_profile.staff_id
        elif u.role_name == "PATIENT" and u.patient_profile:
            name = u.patient_profile.full_name
            profile_id = u.patient_profile.patient_id
            
        res.append({
            "user_id": u.user_id,
            "username": u.username,
            "email": u.email,
            "role": u.role_name,
            "full_name": name,
            "profile_id": profile_id,
            "is_active": u.is_active,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat()
        })
    return res

@router.post("/doctors")
def create_doctor(
    request: Request,
    doc_data: DoctorCreateRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter((User.username == doc_data.username) | (User.email == doc_data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    total_docs = db.query(Doctor).count()
    doctor_id = f"DOC-{total_docs + 101:03d}"

    new_user = User(
        username=doc_data.username,
        email=doc_data.email,
        password_hash=get_password_hash(doc_data.password),
        role_name="DOCTOR",
        is_active=True
    )
    db.add(new_user)
    db.flush()

    new_doctor = Doctor(
        doctor_id=doctor_id,
        user_id=new_user.user_id,
        full_name=doc_data.full_name,
        specialization=doc_data.specialization,
        department=doc_data.department,
        license_number=doc_data.license_number,
        phone=doc_data.phone,
        email=doc_data.email,
        consulting_hours=doc_data.consulting_hours
    )
    db.add(new_doctor)
    db.commit()

    record_audit_event(
        db, current_user.user_id, "ADMIN",
        "CREATE_DOCTOR", "doctors", doctor_id,
        {"email": doc_data.email, "name": doc_data.full_name},
        request.client.host if request.client else None
    )

    return {"message": "Doctor account created successfully", "doctor_id": doctor_id}

@router.post("/staff")
def create_staff(
    request: Request,
    staff_data: StaffCreateRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter((User.username == staff_data.username) | (User.email == staff_data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    total_stf = db.query(Staff).count()
    staff_id = f"STF-{total_stf + 501:03d}"

    new_user = User(
        username=staff_data.username,
        email=staff_data.email,
        password_hash=get_password_hash(staff_data.password),
        role_name="STAFF",
        is_active=True
    )
    db.add(new_user)
    db.flush()

    new_staff = Staff(
        staff_id=staff_id,
        user_id=new_user.user_id,
        full_name=staff_data.full_name,
        department=staff_data.department,
        designation=staff_data.designation,
        phone=staff_data.phone,
        email=staff_data.email
    )
    db.add(new_staff)
    db.commit()

    record_audit_event(
        db, current_user.user_id, "ADMIN",
        "CREATE_STAFF", "staff", staff_id,
        {"email": staff_data.email, "name": staff_data.full_name},
        request.client.host if request.client else None
    )

    return {"message": "Staff account created successfully", "staff_id": staff_id}

@router.put("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate own admin account")

    user.is_active = is_active
    db.commit()
    return {"message": f"User account {'activated' if is_active else 'deactivated'} successfully"}

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = 50,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return logs

@router.post("/execute-query")
def execute_demonstration_query(
    query_payload: Dict[str, str],
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Executes SELECT demonstration queries safely for DBMS academic evaluation.
    Only read-only SELECT queries are allowed.
    """
    sql_text = query_payload.get("query", "").strip()
    if not sql_text.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT demonstration queries are allowed for security.")

    try:
        result = db.execute(text(sql_text))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "status": "SUCCESS"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution error: {str(e)}")
