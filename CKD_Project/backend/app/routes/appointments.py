import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.entities import (
    User, Patient, Doctor, Appointment, DoctorPatientAssignment, Notification
)
from backend.app.schemas.schemas import (
    AppointmentCreate, AppointmentUpdateStatus, AppointmentResponse
)
from backend.app.auth.deps import get_current_user
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.get("", response_model=List[AppointmentResponse])
def get_appointments(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Appointment)
    
    if current_user.role_name == "PATIENT":
        query = query.filter(Appointment.patient_id == current_user.patient_profile.patient_id)
    elif current_user.role_name == "DOCTOR":
        query = query.filter(Appointment.doctor_id == current_user.doctor_profile.doctor_id)
        
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
        
    appointments = query.order_by(Appointment.preferred_date.desc(), Appointment.preferred_time.desc()).all()
    
    results = []
    for a in appointments:
        results.append(AppointmentResponse(
            appointment_id=a.appointment_id,
            patient_id=a.patient_id,
            doctor_id=a.doctor_id,
            department=a.department,
            preferred_date=a.preferred_date,
            preferred_time=a.preferred_time,
            reason_for_visit=a.reason_for_visit,
            status=a.status,
            cancellation_reason=a.cancellation_reason,
            created_at=a.created_at,
            patient_name=a.patient.full_name if a.patient else None,
            doctor_name=a.doctor.full_name if a.doctor else None
        ))
    return results

@router.post("", response_model=AppointmentResponse)
def book_appointment(
    request: Request,
    app_data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Determine Patient ID
    patient_id = None
    if current_user.role_name == "PATIENT":
        patient_id = current_user.patient_profile.patient_id
    elif current_user.role_name in ["ADMIN", "STAFF", "DOCTOR"]:
        # Staff/Doctor booking for patient
        patient_id = request.query_params.get("patient_id")
        if not patient_id:
            raise HTTPException(status_code=400, detail="patient_id query parameter required for staff/admin booking")
            
    # Check Doctor Existence
    doctor = db.query(Doctor).filter(Doctor.doctor_id == app_data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    # Prevent Double-Booking: check if doctor already has an active appointment at that slot
    existing_slot = db.query(Appointment).filter(
        Appointment.doctor_id == app_data.doctor_id,
        Appointment.preferred_date == app_data.preferred_date,
        Appointment.preferred_time == app_data.preferred_time,
        Appointment.status.in_(["Requested", "Confirmed"])
    ).first()
    if existing_slot:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Doctor {doctor.full_name} is already booked on {app_data.preferred_date} at {app_data.preferred_time}. Please select another time slot."
        )

    # Create Appointment
    new_app = Appointment(
        patient_id=patient_id,
        doctor_id=app_data.doctor_id,
        department=app_data.department,
        preferred_date=app_data.preferred_date,
        preferred_time=app_data.preferred_time,
        reason_for_visit=app_data.reason_for_visit,
        status="Requested"
    )
    db.add(new_app)
    
    # Ensure Doctor-Patient Assignment
    existing_assign = db.query(DoctorPatientAssignment).filter(
        DoctorPatientAssignment.patient_id == patient_id,
        DoctorPatientAssignment.doctor_id == app_data.doctor_id
    ).first()
    if not existing_assign:
        db.add(DoctorPatientAssignment(patient_id=patient_id, doctor_id=app_data.doctor_id))

    # Send Notification to Doctor
    if doctor.user:
        db.add(Notification(
            recipient_user_id=doctor.user.user_id,
            title="New Appointment Request",
            message=f"New appointment requested for {app_data.preferred_date} at {app_data.preferred_time}.",
            category="Appointment",
            link_url="/doctor/index.html"
        ))

    db.commit()
    db.refresh(new_app)

    record_audit_event(
        db, current_user.user_id, current_user.role_name,
        "CREATE_APPOINTMENT", "appointments", str(new_app.appointment_id),
        {"patient_id": patient_id, "doctor_id": app_data.doctor_id, "date": str(app_data.preferred_date)},
        request.client.host if request.client else None
    )

    return AppointmentResponse(
        appointment_id=new_app.appointment_id,
        patient_id=new_app.patient_id,
        doctor_id=new_app.doctor_id,
        department=new_app.department,
        preferred_date=new_app.preferred_date,
        preferred_time=new_app.preferred_time,
        reason_for_visit=new_app.reason_for_visit,
        status=new_app.status,
        cancellation_reason=new_app.cancellation_reason,
        created_at=new_app.created_at,
        patient_name=new_app.patient.full_name if new_app.patient else None,
        doctor_name=doctor.full_name
    )

@router.put("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    status_data: AppointmentUpdateStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    # Check permissions
    if current_user.role_name == "PATIENT":
        if app.patient_id != current_user.patient_profile.patient_id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this appointment")
        if status_data.status not in ["Cancelled"]:
            raise HTTPException(status_code=400, detail="Patients may only cancel appointments")
            
    app.status = status_data.status
    if status_data.cancellation_reason:
        app.cancellation_reason = status_data.cancellation_reason
    if status_data.preferred_date:
        app.preferred_date = status_data.preferred_date
    if status_data.preferred_time:
        app.preferred_time = status_data.preferred_time
        
    app.updated_at = datetime.datetime.utcnow()
    
    # Notify Patient on status change
    if app.patient and app.patient.user:
        db.add(Notification(
            recipient_user_id=app.patient.user.user_id,
            title=f"Appointment {status_data.status}",
            message=f"Your appointment with {app.doctor.full_name} on {app.preferred_date} is now {status_data.status}.",
            category="Appointment",
            link_url="/patient/index.html"
        ))

    db.commit()
    db.refresh(app)

    return AppointmentResponse(
        appointment_id=app.appointment_id,
        patient_id=app.patient_id,
        doctor_id=app.doctor_id,
        department=app.department,
        preferred_date=app.preferred_date,
        preferred_time=app.preferred_time,
        reason_for_visit=app.reason_for_visit,
        status=app.status,
        cancellation_reason=app.cancellation_reason,
        created_at=app.created_at,
        patient_name=app.patient.full_name if app.patient else None,
        doctor_name=app.doctor.full_name if app.doctor else None
    )
