import datetime
import random
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_token(username, password):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.json()["access_token"]

def test_appointment_booking_and_double_booking_prevention():
    pat_token = get_auth_token("patient.john@hospital.com", "Patient@123")
    
    # Generate random unique date and slot for test run
    random_days = random.randint(30, 365)
    random_minute = random.randint(10, 59)
    unique_date = (datetime.date.today() + datetime.timedelta(days=random_days)).isoformat()
    unique_time = f"09:{random_minute} AM"

    # 1. Book first appointment
    resp1 = client.post(
        "/api/appointments",
        headers={"Authorization": f"Bearer {pat_token}"},
        json={
            "doctor_id": "DOC-101",
            "department": "Nephrology",
            "preferred_date": unique_date,
            "preferred_time": unique_time,
            "reason_for_visit": "Initial Renal Consultation"
        }
    )
    assert resp1.status_code == 200
    app_id = resp1.json()["appointment_id"]

    # 2. Attempt duplicate double-booking for same doctor, date & time slot
    resp2 = client.post(
        "/api/appointments",
        headers={"Authorization": f"Bearer {pat_token}"},
        json={
            "doctor_id": "DOC-101",
            "department": "Nephrology",
            "preferred_date": unique_date,
            "preferred_time": unique_time,
            "reason_for_visit": "Conflict Double-Booking Test"
        }
    )
    assert resp2.status_code == 409  # Conflict
    assert "already booked" in resp2.json()["detail"].lower()
