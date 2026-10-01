import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models.entities import User, Doctor

client = TestClient(app)

def test_doctors_list_retrieval_and_new_doctor_visibility():
    # 1. Login as patient
    patient_login = client.post("/api/auth/login", json={
        "username": "patient.john@hospital.com",
        "password": "Patient@123"
    })
    assert patient_login.status_code == 200, f"Patient login failed: {patient_login.text}"
    patient_token = patient_login.json()["access_token"]
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    # 2. Get initial doctors list
    initial_res = client.get("/api/doctors/list", headers=patient_headers)
    assert initial_res.status_code == 200
    initial_doctors = initial_res.json()
    assert len(initial_doctors) >= 1
    assert any(d["doctor_id"] == "DOC-101" for d in initial_doctors)

    # 3. Login as admin and create a new doctor
    admin_login = client.post("/api/auth/login", json={
        "username": "admin@hospital.com",
        "password": "Admin@123"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    import time
    unique_user = f"dr_test_{int(time.time())}"
    unique_email = f"dr_test_{int(time.time())}@hospital.com"
    new_doc_data = {
        "username": unique_user,
        "email": unique_email,
        "password": "Doctor@123",
        "full_name": "Dr. Robert Chen, MD",
        "specialization": "Pediatric Nephrology",
        "department": "Renal Medicine",
        "license_number": f"LIC-{int(time.time())}",
        "phone": "+1 (555) 999-8877",
        "consulting_hours": "10:00 AM - 04:00 PM"
    }
    create_res = client.post("/api/admin/doctors", json=new_doc_data, headers=admin_headers)
    assert create_res.status_code == 200, f"Doctor creation failed: {create_res.text}"
    created_doc = create_res.json()
    new_doctor_id = created_doc["doctor_id"]

    # 4. As patient, fetch doctors list again and verify newly created doctor appears
    updated_res = client.get("/api/doctors/list", headers=patient_headers)
    assert updated_res.status_code == 200
    updated_doctors = updated_res.json()
    
    found = next((d for d in updated_doctors if d["doctor_id"] == new_doctor_id), None)
    assert found is not None, f"Newly created doctor {new_doctor_id} was not found in doctors list"
    assert found["full_name"] == "Dr. Robert Chen, MD"
    assert found["specialization"] == "Pediatric Nephrology"