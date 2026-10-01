import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.entities import (
    User, Staff, Patient, LaboratoryTest, LaboratoryResult, MedicalAssessment
)
from backend.app.auth.deps import require_role

router = APIRouter(prefix="/staff", tags=["Staff"])

@router.get("/dashboard-overview")
def get_staff_dashboard_overview(
    current_user: User = Depends(require_role(["STAFF", "ADMIN"])),
    db: Session = Depends(get_db)
):
    staff = current_user.staff_profile
    pending_tests = db.query(LaboratoryTest).filter(
        LaboratoryTest.status.in_(["Requested", "Sample Collected", "Processing"])
    ).count()

    completed_tests = db.query(LaboratoryTest).filter(
        LaboratoryTest.status.in_(["Completed", "Verified"])
    ).count()

    pending_assessments = db.query(MedicalAssessment).count()
    total_patients = db.query(Patient).count()

    recent_requests = db.query(LaboratoryTest).filter(
        LaboratoryTest.status.in_(["Requested", "Sample Collected", "Processing"])
    ).order_by(LaboratoryTest.test_date.desc()).limit(10).all()

    return {
        "staff_name": staff.full_name if staff else "Lab Staff",
        "pending_tests_count": pending_tests,
        "completed_tests_count": completed_tests,
        "pending_assessments_count": pending_assessments,
        "total_patients_count": total_patients,
        "recent_requests": [
            {
                "test_id": lt.test_id,
                "patient_id": lt.patient_id,
                "patient_name": lt.patient.full_name if lt.patient else "Unknown",
                "test_name": lt.test_name,
                "sample_type": lt.sample_type,
                "status": lt.status,
                "test_date": lt.test_date.isoformat(),
                "comments": lt.comments
            } for lt in recent_requests
        ]
    }
