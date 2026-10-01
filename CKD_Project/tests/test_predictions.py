import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_token(username, password):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.json()["access_token"]

def test_ml_model_info():
    response = client.get("/api/predictions/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "active_model" in data
    assert data["active_model"]["model_name"] in ["XGBoost", "LightGBM"]
    assert "metrics" in data["active_model"]

def test_prediction_execution_and_shap():
    doc_token = get_auth_token("doctor.sarah@hospital.com", "Doctor@123")
    response = client.post(
        "/api/predictions/run",
        headers={"Authorization": f"Bearer {doc_token}"},
        json={
            "patient_id": "PAT-001",
            "model_choice": "XGBoost"
        }
    )
    assert response.status_code == 200
    pred = response.json()
    assert pred["prediction_result"] in ["CKD Detected", "No CKD Detected"]
    assert "probability" in pred
    assert "top_factors" in pred
    assert len(pred["top_factors"]) > 0
    assert "shap_explanation" in pred
    assert "clinical_disclaimer" in pred
