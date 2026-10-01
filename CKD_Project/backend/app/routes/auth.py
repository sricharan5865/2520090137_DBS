import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.entities import User, Role, Patient, Doctor, Staff
from backend.app.schemas.schemas import (
    Token, LoginRequest, PatientRegisterRequest, UserResponse
)
from backend.app.core.security import (
    verify_password, get_password_hash, create_access_token
)
from backend.app.auth.deps import get_current_user
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username)
    ).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        record_audit_event(
            db, user.user_id if user else None, None,
            "LOGIN_FAILED", "users", None,
            {"username_attempt": login_data.username}, request.client.host if request.client else None, "FAILED"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact administration."
        )
        
    user.last_login = datetime.datetime.utcnow()
    db.commit()
    
    # Retrieve role profile identifier
    profile_id = None
    full_name = None
    if user.role_name == "PATIENT" and user.patient_profile:
        profile_id = user.patient_profile.patient_id
        full_name = user.patient_profile.full_name
    elif user.role_name == "DOCTOR" and user.doctor_profile:
        profile_id = user.doctor_profile.doctor_id
        full_name = user.doctor_profile.full_name
    elif user.role_name == "STAFF" and user.staff_profile:
        profile_id = user.staff_profile.staff_id
        full_name = user.staff_profile.full_name
    elif user.role_name == "ADMIN":
        profile_id = "ADMIN"
        full_name = "System Administrator"

    token = create_access_token(data={
        "sub": user.username,
        "user_id": user.user_id,
        "role": user.role_name,
        "profile_id": profile_id,
        "full_name": full_name
    })

    record_audit_event(
        db, user.user_id, user.role_name,
        "USER_LOGIN", "users", str(user.user_id),
        {"username": user.username, "role": user.role_name}, request.client.host if request.client else None
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role_name,
        "username": user.username,
        "user_id": user.user_id,
        "profile_id": profile_id,
        "full_name": full_name
    }

# Swagger OAuth2 password form support
@router.post("/token", response_model=Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    login_req = LoginRequest(username=form_data.username, password=form_data.password)
    return login(request, login_req, db)

@router.post("/register/patient", response_model=Token)
def register_patient(
    request: Request,
    reg_data: PatientRegisterRequest,
    db: Session = Depends(get_db)
):
    # Check if username or email exists
    existing_user = db.query(User).filter(
        (User.username == reg_data.username) | (User.email == reg_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
        
    # Generate Unique Patient ID
    total_patients = db.query(Patient).count()
    patient_id = f"PAT-{total_patients + 101:03d}"
    
    # Create User record
    new_user = User(
        username=reg_data.username,
        email=reg_data.email,
        password_hash=get_password_hash(reg_data.password),
        role_name="PATIENT",
        is_active=True
    )
    db.add(new_user)
    db.flush()
    
    # Create Patient record
    new_patient = Patient(
        patient_id=patient_id,
        user_id=new_user.user_id,
        full_name=reg_data.full_name,
        date_of_birth=reg_data.date_of_birth,
        gender=reg_data.gender,
        phone=reg_data.phone,
        email=reg_data.email,
        address=reg_data.address,
        emergency_contact=reg_data.emergency_contact,
        blood_group=reg_data.blood_group
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(data={
        "sub": new_user.username,
        "user_id": new_user.user_id,
        "role": "PATIENT",
        "profile_id": patient_id,
        "full_name": new_patient.full_name
    })

    record_audit_event(
        db, new_user.user_id, "PATIENT",
        "PATIENT_REGISTER", "patients", patient_id,
        {"email": reg_data.email, "full_name": reg_data.full_name},
        request.client.host if request.client else None
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "PATIENT",
        "username": new_user.username,
        "user_id": new_user.user_id,
        "profile_id": patient_id,
        "full_name": new_patient.full_name
    }

@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile_data = {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "role_name": current_user.role_name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }
    
    if current_user.role_name == "PATIENT" and current_user.patient_profile:
        p = current_user.patient_profile
        profile_data.update({
            "patient_id": p.patient_id,
            "full_name": p.full_name,
            "date_of_birth": p.date_of_birth,
            "gender": p.gender,
            "phone": p.phone,
            "address": p.address,
            "emergency_contact": p.emergency_contact,
            "blood_group": p.blood_group
        })
    elif current_user.role_name == "DOCTOR" and current_user.doctor_profile:
        d = current_user.doctor_profile
        profile_data.update({
            "doctor_id": d.doctor_id,
            "full_name": d.full_name,
            "specialization": d.specialization,
            "department": d.department,
            "license_number": d.license_number,
            "phone": d.phone,
            "consulting_hours": d.consulting_hours
        })
    elif current_user.role_name == "STAFF" and current_user.staff_profile:
        s = current_user.staff_profile
        profile_data.update({
            "staff_id": s.staff_id,
            "full_name": s.full_name,
            "department": s.department,
            "designation": s.designation,
            "phone": s.phone
        })
    elif current_user.role_name == "ADMIN":
        profile_data.update({
            "profile_id": "ADMIN",
            "full_name": "System Administrator"
        })
        
    return profile_data
