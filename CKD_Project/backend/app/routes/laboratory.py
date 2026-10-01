import os
import shutil
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from backend.app.database.session import get_db, get_mongo_db
from backend.app.core.config import settings
from backend.app.models.entities import (
    User, Patient, Staff, Doctor, LaboratoryTest, LaboratoryResult, Notification
)
from backend.app.schemas.schemas import (
    LaboratoryTestCreate, LaboratoryTestEnterResults, LaboratoryTestResponse, LaboratoryResultResponse
)
from backend.app.auth.deps import get_current_user, require_role
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/laboratory", tags=["Laboratory"])

@router.get("/tests", response_model=List[LaboratoryTestResponse])
def get_lab_tests(
    status_filter: Optional[str] = None,
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(LaboratoryTest)
    
    if current_user.role_name == "PATIENT":
        query = query.filter(LaboratoryTest.patient_id == current_user.patient_profile.patient_id)
    elif patient_id:
        query = query.filter(LaboratoryTest.patient_id == patient_id)
        
    if status_filter:
        query = query.filter(LaboratoryTest.status == status_filter)
        
    tests = query.order_by(LaboratoryTest.test_date.desc()).all()
    
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
            patient_name=t.patient.full_name if t.patient else None,
            staff_name=t.staff.full_name if t.staff else "Unassigned",
            doctor_name=t.doctor.full_name if t.doctor else "Not assigned",
            results=[
                LaboratoryResultResponse(
                    result_id=r.result_id,
                    test_id=r.test_id,
                    parameter_name=r.parameter_name,
                    parameter_code=r.parameter_code,
                    test_value=float(r.test_value),
                    unit=r.unit,
                    reference_range=r.reference_range,
                    abnormal_status=r.abnormal_status,
                    created_at=r.created_at
                ) for r in t.results
            ]
        ))
    return res

@router.post("/tests", response_model=LaboratoryTestResponse)
def create_lab_test_request(
    request: Request,
    test_data: LaboratoryTestCreate,
    current_user: User = Depends(require_role(["DOCTOR", "STAFF", "ADMIN"])),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.patient_id == test_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    doctor_id = test_data.doctor_id
    if current_user.role_name == "DOCTOR" and not doctor_id:
        doctor_id = current_user.doctor_profile.doctor_id

    new_test = LaboratoryTest(
        patient_id=test_data.patient_id,
        doctor_id=doctor_id,
        test_name=test_data.test_name,
        sample_type=test_data.sample_type,
        comments=test_data.comments,
        status="Requested"
    )
    db.add(new_test)
    db.commit()
    db.refresh(new_test)

    return LaboratoryTestResponse(
        test_id=new_test.test_id,
        patient_id=new_test.patient_id,
        staff_id=new_test.staff_id,
        doctor_id=new_test.doctor_id,
        test_name=new_test.test_name,
        sample_type=new_test.sample_type,
        test_date=new_test.test_date,
        status=new_test.status,
        report_file_url=new_test.report_file_url,
        comments=new_test.comments,
        created_at=new_test.created_at,
        patient_name=patient.full_name,
        results=[]
    )

@router.post("/tests/{test_id}/results", response_model=LaboratoryTestResponse)
def enter_lab_results(
    request: Request,
    test_id: int,
    results_data: LaboratoryTestEnterResults,
    current_user: User = Depends(require_role(["STAFF", "ADMIN"])),
    db: Session = Depends(get_db)
):
    test = db.query(LaboratoryTest).filter(LaboratoryTest.test_id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Laboratory test not found")
        
    staff_id = current_user.staff_profile.staff_id if current_user.role_name == "STAFF" else (results_data.staff_id or "STF-501")
    test.staff_id = staff_id
    test.status = results_data.status or "Completed"
    if results_data.comments:
        test.comments = results_data.comments
    test.updated_at = datetime.datetime.utcnow()

    # Clear existing results if re-entering
    db.query(LaboratoryResult).filter(LaboratoryResult.test_id == test_id).delete()

    for item in results_data.results:
        lab_res = LaboratoryResult(
            test_id=test_id,
            parameter_name=item.parameter_name,
            parameter_code=item.parameter_code,
            test_value=item.test_value,
            unit=item.unit,
            reference_range=item.reference_range,
            abnormal_status=item.abnormal_status
        )
        db.add(lab_res)
        
    db.commit()
    db.refresh(test)
    
    saved_results = db.query(LaboratoryResult).filter(LaboratoryResult.test_id == test_id).all()

    record_audit_event(
        db, current_user.user_id, current_user.role_name,
        "ENTER_LAB_RESULTS", "laboratory_tests", str(test_id),
        {"patient_id": test.patient_id, "params_count": len(results_data.results)},
        request.client.host if request.client else None
    )

    return LaboratoryTestResponse(
        test_id=test.test_id,
        patient_id=test.patient_id,
        staff_id=test.staff_id,
        doctor_id=test.doctor_id,
        test_name=test.test_name,
        sample_type=test.sample_type,
        test_date=test.test_date,
        status=test.status,
        report_file_url=test.report_file_url,
        comments=test.comments,
        created_at=test.created_at,
        patient_name=test.patient.full_name if test.patient else None,
        staff_name=test.staff.full_name if test.staff else None,
        doctor_name=test.doctor.full_name if test.doctor else None,
        results=[
            LaboratoryResultResponse(
                result_id=r.result_id,
                test_id=r.test_id,
                parameter_name=r.parameter_name,
                parameter_code=r.parameter_code,
                test_value=float(r.test_value),
                unit=r.unit,
                reference_range=r.reference_range,
                abnormal_status=r.abnormal_status,
                created_at=r.created_at
            ) for r in saved_results
        ]
    )

@router.post("/tests/{test_id}/upload-report")
def upload_lab_report(
    test_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["STAFF", "ADMIN"])),
    db: Session = Depends(get_db)
):
    test = db.query(LaboratoryTest).filter(LaboratoryTest.test_id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Laboratory test not found")

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
        raise HTTPException(status_code=400, detail="Only PDF and Image files (.png, .jpg, .jpeg) are allowed")

    filename = f"lab_report_{test_id}_{int(datetime.datetime.utcnow().timestamp())}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    report_url = f"/uploads/{filename}"
    test.report_file_url = report_url
    test.updated_at = datetime.datetime.utcnow()
    db.commit()

    return {"message": "Report file uploaded successfully", "report_url": report_url}

@router.put("/tests/{test_id}/verify")
def verify_lab_test(
    request: Request,
    test_id: int,
    current_user: User = Depends(require_role(["STAFF", "ADMIN"])),
    db: Session = Depends(get_db)
):
    test = db.query(LaboratoryTest).filter(LaboratoryTest.test_id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Laboratory test not found")

    test.status = "Verified"
    test.staff_id = current_user.staff_profile.staff_id if current_user.role_name == "STAFF" else (test.staff_id or "STF-501")
    test.updated_at = datetime.datetime.utcnow()

    # Notify Patient
    if test.patient and test.patient.user:
        db.add(Notification(
            recipient_user_id=test.patient.user.user_id,
            title="Lab Report Verified & Available",
            message=f"Your laboratory results for {test.test_name} have been verified.",
            category="Laboratory",
            link_url="/patient/index.html"
        ))

    # Notify Doctor
    if test.doctor and test.doctor.user:
        db.add(Notification(
            recipient_user_id=test.doctor.user.user_id,
            title="Verified Lab Report Ready",
            message=f"Verified lab report for Patient {test.patient.full_name} ({test.patient_id}) is ready for review.",
            category="Laboratory",
            link_url="/doctor/index.html"
        ))

    db.commit()

    record_audit_event(
        db, current_user.user_id, current_user.role_name,
        "VERIFY_LAB_REPORT", "laboratory_tests", str(test_id),
        {"patient_id": test.patient_id, "test_name": test.test_name},
        request.client.host if request.client else None
    )

    return {"message": "Laboratory test report verified and forwarded to doctor", "status": "Verified"}
