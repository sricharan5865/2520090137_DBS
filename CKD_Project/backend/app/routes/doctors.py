import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.database.session import get_db, get_mongo_db
from backend.app.models.entities import (
    User, Doctor, Patient, Appointment, MedicalAssessment, LaboratoryTest, PredictionRecord, ClinicalNote, Notification
)
from backend.app.schemas.schemas import (
    ClinicalNoteCreate, ClinicalNoteResponse, AppointmentResponse, LaboratoryTestResponse, PredictionResponse, DoctorResponse
)
from backend.app.auth.deps import get_current_user, require_role
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/doctors", tags=["Doctors"])

@router.get("", response_model=List[DoctorResponse])
@router.get("/list", response_model=List[DoctorResponse])
def get_doctors_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all active medical doctors for appointment booking and clinical assignment.
    """
    doctors = (
        db.query(Doctor)
        .join(User, Doctor.user_id == User.user_id)
        .filter(User.is_active == True)
        .order_by(Doctor.full_name.asc())
        .all()
    )
    return [
        DoctorResponse(
            doctor_id=d.doctor_id,
            full_name=d.full_name,
            specialization=d.specialization,
            department=d.department,
            email=d.email,
            phone=d.phone,
            consulting_hours=d.consulting_hours
        )
        for d in doctors
    ]

@router.get("/dashboard-overview")
def get_doctor_dashboard_overview(
    current_user: User = Depends(require_role(["DOCTOR"])),
    db: Session = Depends(get_db)
):
    doctor = current_user.doctor_profile
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    today = datetime.date.today()
    today_appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor.doctor_id,
        Appointment.preferred_date == today
    ).count()

    total_patients = db.query(Appointment.patient_id).filter(
        Appointment.doctor_id == doctor.doctor_id
    ).distinct().count()

    pending_reviews = db.query(LaboratoryTest).filter(
        LaboratoryTest.status.in_(["Completed", "Verified"])
    ).count()

    total_predictions = db.query(PredictionRecord).filter(
        PredictionRecord.doctor_id == doctor.doctor_id
    ).count()

    # Upcoming appointments
    upcoming = db.query(Appointment).filter(
        Appointment.doctor_id == doctor.doctor_id,
        Appointment.status.in_(["Requested", "Confirmed"])
    ).order_by(Appointment.preferred_date.asc(), Appointment.preferred_time.asc()).limit(5).all()

    # Recent predictions
    recent_preds = db.query(PredictionRecord).filter(
        PredictionRecord.doctor_id == doctor.doctor_id
    ).order_by(PredictionRecord.created_at.desc()).limit(5).all()

    return {
        "doctor_id": doctor.doctor_id,
        "doctor_name": doctor.full_name,
        "specialization": doctor.specialization,
        "department": doctor.department,
        "today_appointments_count": today_appointments,
        "total_patients_count": total_patients,
        "pending_reviews_count": pending_reviews,
        "total_predictions_count": total_predictions,
        "upcoming_appointments": [
            {
                "appointment_id": a.appointment_id,
                "patient_id": a.patient_id,
                "patient_name": a.patient.full_name if a.patient else "Unknown",
                "date": a.preferred_date.isoformat(),
                "time": a.preferred_time,
                "reason": a.reason_for_visit,
                "status": a.status
            } for a in upcoming
        ],
        "recent_predictions": [
            {
                "prediction_id": p.prediction_id,
                "patient_id": p.patient_id,
                "patient_name": p.patient.full_name if p.patient else "Unknown",
                "result": p.prediction_result,
                "probability": float(p.probability),
                "risk_level": p.risk_level,
                "date": p.created_at.isoformat()
            } for p in recent_preds
        ]
    }

@router.get("/patients/search")
def search_patients(
    q: Optional[str] = None,
    current_user: User = Depends(require_role(["DOCTOR", "ADMIN", "STAFF"])),
    db: Session = Depends(get_db)
):
    query = db.query(Patient)
    if q:
        query = query.filter(
            or_(
                Patient.patient_id.ilike(f"%{q}%"),
                Patient.full_name.ilike(f"%{q}%"),
                Patient.phone.ilike(f"%{q}%"),
                Patient.email.ilike(f"%{q}%")
            )
        )
    patients = query.order_by(Patient.patient_id.asc()).limit(200).all()
    return [
        {
            "patient_id": p.patient_id,
            "full_name": p.full_name,
            "date_of_birth": p.date_of_birth.isoformat(),
            "gender": p.gender,
            "phone": p.phone,
            "email": p.email,
            "blood_group": p.blood_group
        } for p in patients
    ]

@router.get("/patients/{patient_id}/360")
def get_patient_360_record(
    patient_id: str,
    current_user: User = Depends(require_role(["DOCTOR", "ADMIN", "STAFF"])),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Demographics & Assessment
    assessments = db.query(MedicalAssessment).filter(
        MedicalAssessment.patient_id == patient_id
    ).order_by(MedicalAssessment.created_at.desc()).all()

    # Lab Tests & Results
    lab_tests = db.query(LaboratoryTest).filter(
        LaboratoryTest.patient_id == patient_id
    ).order_by(LaboratoryTest.test_date.desc()).all()

    # Appointments
    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id
    ).order_by(Appointment.preferred_date.desc()).all()

    # Predictions
    predictions = db.query(PredictionRecord).filter(
        PredictionRecord.patient_id == patient_id
    ).order_by(PredictionRecord.created_at.desc()).all()

    # Clinical Notes
    notes = db.query(ClinicalNote).filter(
        ClinicalNote.patient_id == patient_id
    ).order_by(ClinicalNote.created_at.desc()).all()

    # Check MongoDB for flexible unstructured observations if enabled
    mongo_notes = []
    mongo = get_mongo_db()
    if mongo is not None:
        try:
            m_docs = mongo.clinical_notes.find({"patient_id": patient_id}).sort("timestamp", -1)
            for md in m_docs:
                mongo_notes.append({
                    "id": str(md.get("_id")),
                    "author": md.get("author", "Doctor"),
                    "note": md.get("note", ""),
                    "timestamp": md.get("timestamp", "").isoformat() if hasattr(md.get("timestamp"), "isoformat") else str(md.get("timestamp"))
                })
        except Exception as e:
            print(f"Mongo fetch error: {e}")

    return {
        "patient": {
            "patient_id": patient.patient_id,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth.isoformat(),
            "gender": patient.gender,
            "phone": patient.phone,
            "email": patient.email,
            "address": patient.address,
            "emergency_contact": patient.emergency_contact,
            "blood_group": patient.blood_group
        },
        "latest_assessment": assessments[0] if assessments else None,
        "all_assessments_count": len(assessments),
        "lab_tests": [
            {
                "test_id": lt.test_id,
                "test_name": lt.test_name,
                "sample_type": lt.sample_type,
                "status": lt.status,
                "test_date": lt.test_date.isoformat(),
                "report_file_url": lt.report_file_url,
                "comments": lt.comments,
                "results": [
                    {
                        "parameter_name": r.parameter_name,
                        "parameter_code": r.parameter_code,
                        "test_value": float(r.test_value),
                        "unit": r.unit,
                        "reference_range": r.reference_range,
                        "abnormal_status": r.abnormal_status
                    } for r in lt.results
                ]
            } for lt in lab_tests
        ],
        "appointments": [
            {
                "appointment_id": a.appointment_id,
                "doctor_name": a.doctor.full_name if a.doctor else "Unknown",
                "date": a.preferred_date.isoformat(),
                "time": a.preferred_time,
                "status": a.status,
                "reason": a.reason_for_visit
            } for a in appointments
        ],
        "predictions": [
            {
                "prediction_id": p.prediction_id,
                "model_name": p.model_name,
                "model_version": p.model_version,
                "result": p.prediction_result,
                "probability": float(p.probability),
                "risk_level": p.risk_level,
                "top_factors": p.top_factors_json,
                "date": p.created_at.isoformat()
            } for p in predictions
        ],
        "clinical_notes": [
            {
                "note_id": n.note_id,
                "doctor_name": n.doctor.full_name if n.doctor else "Doctor",
                "clinical_summary": n.clinical_summary,
                "diagnosis": n.diagnosis,
                "treatment_plan": n.treatment_plan,
                "prescriptions": n.prescriptions,
                "follow_up_date": n.follow_up_date.isoformat() if n.follow_up_date else None,
                "created_at": n.created_at.isoformat()
            } for n in notes
        ],
        "mongodb_clinical_documents": mongo_notes
    }

@router.post("/clinical-notes", response_model=ClinicalNoteResponse)
def add_clinical_notes(
    request: Request,
    note_data: ClinicalNoteCreate,
    current_user: User = Depends(require_role(["DOCTOR"])),
    db: Session = Depends(get_db)
):
    doctor = current_user.doctor_profile
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    patient = db.query(Patient).filter(Patient.patient_id == note_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    new_note = ClinicalNote(
        patient_id=note_data.patient_id,
        doctor_id=doctor.doctor_id,
        appointment_id=note_data.appointment_id,
        prediction_id=note_data.prediction_id,
        clinical_summary=note_data.clinical_summary,
        diagnosis=note_data.diagnosis,
        treatment_plan=note_data.treatment_plan,
        prescriptions=note_data.prescriptions,
        follow_up_date=note_data.follow_up_date
    )
    db.add(new_note)

    # Also store in MongoDB if enabled for document flexibility
    mongo = get_mongo_db()
    if mongo is not None:
        try:
            mongo.clinical_notes.insert_one({
                "patient_id": note_data.patient_id,
                "doctor_id": doctor.doctor_id,
                "author": doctor.full_name,
                "diagnosis": note_data.diagnosis,
                "treatment_plan": note_data.treatment_plan,
                "prescriptions": note_data.prescriptions,
                "summary": note_data.clinical_summary,
                "timestamp": datetime.datetime.utcnow()
            })
        except Exception as e:
            print(f"MongoDB Note Insert Error: {e}")

    # Notify patient
    if patient.user:
        db.add(Notification(
            recipient_user_id=patient.user.user_id,
            title="Doctor Consultation Notes Updated",
            message=f"{doctor.full_name} added clinical notes and treatment recommendations.",
            category="Clinical",
            link_url="/patient/index.html"
        ))

    db.commit()
    db.refresh(new_note)

    record_audit_event(
        db, current_user.user_id, "DOCTOR",
        "ADD_CLINICAL_NOTE", "clinical_notes", str(new_note.note_id),
        {"patient_id": patient.patient_id, "diagnosis": note_data.diagnosis},
        request.client.host if request.client else None
    )

    return ClinicalNoteResponse(
        note_id=new_note.note_id,
        patient_id=new_note.patient_id,
        doctor_id=new_note.doctor_id,
        appointment_id=new_note.appointment_id,
        prediction_id=new_note.prediction_id,
        clinical_summary=new_note.clinical_summary,
        diagnosis=new_note.diagnosis,
        treatment_plan=new_note.treatment_plan,
        prescriptions=new_note.prescriptions,
        follow_up_date=new_note.follow_up_date,
        created_at=new_note.created_at,
        doctor_name=doctor.full_name
    )
