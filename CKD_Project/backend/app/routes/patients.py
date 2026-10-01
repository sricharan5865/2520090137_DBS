import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.entities import (
    User, Patient, MedicalAssessment, Appointment, LaboratoryTest, PredictionRecord, ClinicalNote, Notification
)
from backend.app.schemas.schemas import (
    PatientProfileResponse, PatientProfileUpdate, MedicalAssessmentCreate,
    MedicalAssessmentResponse, AppointmentResponse, LaboratoryTestResponse, PredictionResponse
)
from backend.app.auth.deps import get_current_user, require_role
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("/me/profile", response_model=PatientProfileResponse)
def get_my_patient_profile(
    current_user: User = Depends(require_role(["PATIENT"])),
    db: Session = Depends(get_db)
):
    patient = current_user.patient_profile
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return patient

@router.put("/me/profile", response_model=PatientProfileResponse)
def update_my_patient_profile(
    profile_update: PatientProfileUpdate,
    current_user: User = Depends(require_role(["PATIENT"])),
    db: Session = Depends(get_db)
):
    patient = current_user.patient_profile
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
        
    for field, val in profile_update.model_dump(exclude_unset=True).items():
        setattr(patient, field, val)
        
    patient.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(patient)
    return patient

@router.post("/me/assessment", response_model=MedicalAssessmentResponse)
def submit_medical_assessment(
    request: Request,
    assessment_data: MedicalAssessmentCreate,
    current_user: User = Depends(require_role(["PATIENT"])),
    db: Session = Depends(get_db)
):
    patient = current_user.patient_profile
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
        
    # Create Assessment
    assessment_dict = assessment_data.model_dump(exclude={"patient_id"})
    new_assessment = MedicalAssessment(
        patient_id=patient.patient_id,
        **assessment_dict,
        created_at=datetime.datetime.utcnow()
    )
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)

    # Automatically create a Lab Test request for staff queue
    lab_test = LaboratoryTest(
        patient_id=patient.patient_id,
        test_name="Renal Function & Metabolic Panel (CKD Screen)",
        sample_type="Blood & Urine",
        status="Requested",
        comments="Auto-generated from patient medical assessment submission."
    )
    db.add(lab_test)
    
    # Notify staff users
    staff_users = db.query(User).filter(User.role_name == "STAFF").all()
    for stf in staff_users:
        db.add(Notification(
            recipient_user_id=stf.user_id,
            title="New Patient Assessment & Lab Request",
            message=f"Patient {patient.full_name} ({patient.patient_id}) submitted clinical assessment data. Lab test queued.",
            category="Laboratory",
            link_url="/staff/index.html"
        ))
    db.commit()

    record_audit_event(
        db, current_user.user_id, "PATIENT",
        "SUBMIT_ASSESSMENT", "medical_assessments", str(new_assessment.assessment_id),
        {"patient_id": patient.patient_id}, request.client.host if request.client else None
    )

    return new_assessment

@router.get("/me/assessments", response_model=List[MedicalAssessmentResponse])
def get_my_assessments(
    current_user: User = Depends(require_role(["PATIENT"])),
    db: Session = Depends(get_db)
):
    patient = current_user.patient_profile
    return db.query(MedicalAssessment).filter(
        MedicalAssessment.patient_id == patient.patient_id
    ).order_by(MedicalAssessment.created_at.desc()).all()

@router.get("/me/lab-reports", response_model=List[LaboratoryTestResponse])
def get_my_lab_reports(
    current_user: User = Depends(require_role(["PATIENT"])),
    db: Session = Depends(get_db)
):
    patient = current_user.patient_profile
    tests = db.query(LaboratoryTest).filter(
        LaboratoryTest.patient_id == patient.patient_id
    ).order_by(LaboratoryTest.test_date.desc()).all()
    
    # Format response
    res = []
    for t in tests:
        res.append(LaboratoryTestResponse(
            test_id=t.test_id,
            patient_id=t.patient_id,
            staff_id=t.staff_id,
            doctor_id=t.doctor_id,
            test_name=t.test_name,
            sample_type=t.sample_type,
            test_date=t.test_date,
            status=t.status,
            report_file_url=t.report_file_url,
            comments=t.comments,
            created_at=t.created_at,
            patient_name=patient.full_name,
            staff_name=t.staff.full_name if t.staff else "Unassigned",
            doctor_name=t.doctor.full_name if t.doctor else "Not assigned",
            results=[
                {
                    "result_id": r.result_id,
                    "test_id": r.test_id,
                    "parameter_name": r.parameter_name,
                    "parameter_code": r.parameter_code,
                    "test_value": float(r.test_value),
                    "unit": r.unit,
                    "reference_range": r.reference_range,
                    "abnormal_status": r.abnormal_status,
                    "created_at": r.created_at
                } for r in t.results
            ]
        ))
    return res

@router.get("/me/predictions", response_model=List[PredictionResponse])
def get_my_predictions(
    current_user: User = Depends(require_role(["PATIENT"])),
    db: Session = Depends(get_db)
):
    patient = current_user.patient_profile
    preds = db.query(PredictionRecord).filter(
        PredictionRecord.patient_id == patient.patient_id
    ).order_by(PredictionRecord.created_at.desc()).all()
    
    out = []
    for p in preds:
        out.append(PredictionResponse(
            prediction_id=p.prediction_id,
            patient_id=p.patient_id,
            doctor_id=p.doctor_id,
            model_name=p.model_name,
            model_version=p.model_version,
            prediction_result=p.prediction_result,
            probability=float(p.probability),
            risk_level=p.risk_level,
            top_factors=p.top_factors_json,
            shap_explanation=p.shap_explanation_json,
            clinical_disclaimer=p.clinical_disclaimer,
            created_at=p.created_at
        ))
    return out

@router.get("/me/dashboard-overview")
def get_patient_dashboard_overview(
    current_user: User = Depends(require_role(["PATIENT"])),
    db: Session = Depends(get_db)
):
    patient = current_user.patient_profile
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
        
    latest_app = db.query(Appointment).filter(
        Appointment.patient_id == patient.patient_id,
        Appointment.status.in_(["Confirmed", "Requested"])
    ).order_by(Appointment.preferred_date.asc()).first()
    
    latest_lab = db.query(LaboratoryTest).filter(
        LaboratoryTest.patient_id == patient.patient_id
    ).order_by(LaboratoryTest.test_date.desc()).first()
    
    latest_pred = db.query(PredictionRecord).filter(
        PredictionRecord.patient_id == patient.patient_id
    ).order_by(PredictionRecord.created_at.desc()).first()
    
    latest_note = db.query(ClinicalNote).filter(
        ClinicalNote.patient_id == patient.patient_id
    ).order_by(ClinicalNote.created_at.desc()).first()
    
    total_apps = db.query(Appointment).filter(Appointment.patient_id == patient.patient_id).count()
    total_labs = db.query(LaboratoryTest).filter(LaboratoryTest.patient_id == patient.patient_id).count()
    
    return {
        "patient_id": patient.patient_id,
        "full_name": patient.full_name,
        "email": patient.email,
        "blood_group": patient.blood_group,
        "total_appointments": total_apps,
        "total_lab_tests": total_labs,
        "upcoming_appointment": {
            "id": latest_app.appointment_id,
            "doctor": latest_app.doctor.full_name,
            "date": latest_app.preferred_date.isoformat(),
            "time": latest_app.preferred_time,
            "status": latest_app.status
        } if latest_app else None,
        "latest_lab_test": {
            "id": latest_lab.test_id,
            "name": latest_lab.test_name,
            "status": latest_lab.status,
            "date": latest_lab.test_date.isoformat()
        } if latest_lab else None,
        "latest_prediction": {
            "id": latest_pred.prediction_id,
            "result": latest_pred.prediction_result,
            "probability": float(latest_pred.probability),
            "risk_level": latest_pred.risk_level,
            "date": latest_pred.created_at.isoformat()
        } if latest_pred else None,
        "latest_clinical_note": {
            "doctor": latest_note.doctor.full_name,
            "diagnosis": latest_note.diagnosis,
            "treatment_plan": latest_note.treatment_plan,
            "follow_up_date": latest_note.follow_up_date.isoformat() if latest_note.follow_up_date else None
        } if latest_note else None
    }
