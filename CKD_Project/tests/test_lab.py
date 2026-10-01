import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_token(username, password):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.json()["access_token"]

def test_lab_workflow_entry_and_verification():
    stf_token = get_auth_token("staff.james@hospital.com", "Staff@123")
    
    # 1. Fetch pending tests
    tests_resp = client.get("/api/laboratory/tests", headers={"Authorization": f"Bearer {stf_token}"})
    assert tests_resp.status_code == 200
    tests = tests_resp.json()
    assert len(tests) > 0
    target_test_id = tests[0]["test_id"]

    # 2. Enter lab parameters
    enter_resp = client.post(
        f"/api/laboratory/tests/{target_test_id}/results",
        headers={"Authorization": f"Bearer {stf_token}"},
        json={
            "results": [
                {
                    "parameter_name": "Serum Creatinine",
                    "parameter_code": "SC",
                    "test_value": 1.15,
                    "unit": "mg/dL",
                    "reference_range": "0.6 - 1.2",
                    "abnormal_status": "Normal"
                },
                {
                    "parameter_name": "Blood Urea",
                    "parameter_code": "BU",
                    "test_value": 18.0,
                    "unit": "mg/dL",
                    "reference_range": "7 - 20",
                    "abnormal_status": "Normal"
                }
            ],
            "comments": "Automated Spectrometry Test Verified."
        }
    )
    assert enter_resp.status_code == 200
    assert len(enter_resp.json()["results"]) == 2

    # 3. Verify Test
    verify_resp = client.put(
        f"/api/laboratory/tests/{target_test_id}/verify",
        headers={"Authorization": f"Bearer {stf_token}"}
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "Verified"
