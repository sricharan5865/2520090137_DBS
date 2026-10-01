import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token, decode_access_token

client = TestClient(app)

def test_login_success():
    response = client.post("/api/auth/login", json={
        "username": "admin@hospital.com",
        "password": "Admin@123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "ADMIN"
    assert data["token_type"] == "bearer"

def test_login_invalid_password():
    response = client.post("/api/auth/login", json={
        "username": "admin@hospital.com",
        "password": "WrongPassword!999"
    })
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]

def test_patient_registration_flow():
    import uuid
    rand_user = f"testpat_{uuid.uuid4().hex[:6]}"
    response = client.post("/api/auth/register/patient", json={
        "username": rand_user,
        "email": f"{rand_user}@test.com",
        "password": "Patient@123",
        "full_name": "Test Patient Flow",
        "date_of_birth": "1990-01-01",
        "gender": "Male",
        "phone": "+1 555-0199",
        "address": "123 Test St",
        "emergency_contact": "Jane Doe 555-0198",
        "blood_group": "O+"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "PATIENT"
    assert "PAT-" in data["profile_id"]

def test_rbac_unauthorized_access():
    # Attempt to access admin routes without a token
    response = client.get("/api/admin/overview")
    assert response.status_code == 401
