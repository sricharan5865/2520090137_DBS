import os
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.entities import (
    User, Patient, Doctor, MedicalAssessment, PredictionRecord, Notification
)
from backend.app.schemas.schemas import (
    PredictionRunRequest, PredictionResponse
)
from backend.app.auth.deps import get_current_user, require_role
from backend.app.services.ml_service import ml_service
from backend.app.services.audit_service import record_audit_event
from ml.preprocessing.pipeline import ALL_FEATURES

router = APIRouter(prefix="/predictions", tags=["Predictions & ML"])

@router.post("/run", response_model=PredictionResponse)
def run_ckd_prediction(
    request: Request,
    pred_req: PredictionRunRequest,
    current_user: User = Depends(require_role(["DOCTOR", "ADMIN"])),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.patient_id == pred_req.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    doctor_id = pred_req.doctor_id
    if current_user.role_name == "DOCTOR" and not doctor_id:
        doctor_id = current_user.doctor_profile.doctor_id

    # Retrieve patient's latest medical assessment or use specified assessment
    assessment = None
    if pred_req.assessment_id:
        assessment = db.query(MedicalAssessment).filter(
            MedicalAssessment.assessment_id == pred_req.assessment_id
        ).first()
    else:
        assessment = db.query(MedicalAssessment).filter(
            MedicalAssessment.patient_id == pred_req.patient_id
        ).order_by(MedicalAssessment.created_at.desc()).first()

    # Build clinical feature map
    features_dict = {}
    if assessment:
        for feat in ALL_FEATURES:
            val = getattr(assessment, feat, None)
            if val is not None:
                features_dict[feat] = float(val) if isinstance(val, (int, float)) else str(val)

    # Apply any dynamic feature overrides if doctor adjusted values during review
    if pred_req.override_features:
        for k, v in pred_req.override_features.items():
            features_dict[k] = v

    if not features_dict:
        raise HTTPException(
            status_code=400,
            detail="No medical assessment data found for this patient. Please ensure an assessment is submitted or provide clinical features."
        )

    # Run ML Inference + SHAP Explainability
    ml_output = ml_service.run_prediction(features_dict, model_choice=pred_req.model_choice or "XGBoost")

    # Save to Database
    new_pred = PredictionRecord(
        patient_id=patient.patient_id,
        doctor_id=doctor_id,
        assessment_id=assessment.assessment_id if assessment else None,
        model_name=ml_output["model_name"],
        model_version=ml_output["model_version"],
        prediction_result=ml_output["prediction_result"],
        probability=ml_output["probability"],
        risk_level=ml_output["risk_level"],
        top_factors_json=ml_output["top_factors"],
        shap_explanation_json=ml_output["shap_explanation"],
        clinical_disclaimer=ml_output["clinical_disclaimer"]
    )
    db.add(new_pred)

    # Notify Patient that prediction analysis is updated
    if patient.user:
        db.add(Notification(
            recipient_user_id=patient.user.user_id,
            title="CKD Risk Assessment Updated",
            message=f"A new CKD risk prediction analysis has been reviewed by your clinical team. Result: {ml_output['prediction_result']}.",
            category="Prediction",
            link_url="/patient/index.html"
        ))

    db.commit()
    db.refresh(new_pred)

    record_audit_event(
        db, current_user.user_id, current_user.role_name,
        "RUN_CKD_PREDICTION", "prediction_records", str(new_pred.prediction_id),
        {"patient_id": patient.patient_id, "result": ml_output["prediction_result"], "prob": ml_output["probability"]},
        request.client.host if request.client else None
    )

    return PredictionResponse(
        prediction_id=new_pred.prediction_id,
        patient_id=new_pred.patient_id,
        doctor_id=new_pred.doctor_id,
        model_name=new_pred.model_name,
        model_version=new_pred.model_version,
        prediction_result=new_pred.prediction_result,
        probability=float(new_pred.probability),
        risk_level=new_pred.risk_level,
        top_factors=new_pred.top_factors_json,
        shap_explanation=new_pred.shap_explanation_json,
        clinical_disclaimer=new_pred.clinical_disclaimer,
        created_at=new_pred.created_at
    )

@router.get("/history/{patient_id}", response_model=List[PredictionResponse])
def get_patient_prediction_history(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role_name == "PATIENT" and current_user.patient_profile.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="Not authorized to view other patient's predictions")

    preds = db.query(PredictionRecord).filter(
        PredictionRecord.patient_id == patient_id
    ).order_by(PredictionRecord.created_at.desc()).all()

    return [
        PredictionResponse(
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
        ) for p in preds
    ]

@router.get("/model-info")
def get_ml_model_info():
    """Returns metadata about the active ML models and dataset."""
    import json
    metadata_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../ml/models/metadata.json'))
    comparison_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../ml/evaluation/model_comparison.json'))
    
    meta = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            meta = json.load(f)
            
    comp = {}
    if os.path.exists(comparison_path):
        with open(comparison_path, 'r') as f:
            comp = json.load(f)
            
    return {
        "active_model": meta,
        "model_comparison": comp
    }
