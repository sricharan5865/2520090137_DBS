import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_token(username, password):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.json()["access_token"]

def test_demonstration_sql_query_execution():
    adm_token = get_auth_token("admin@hospital.com", "Admin@123")
    
    # Run a relational demonstration query
    query = """
    SELECT a.appointment_id, p.patient_id, p.full_name AS patient_name, d.doctor_id, d.full_name AS doctor_name, a.status
    FROM appointments a
    INNER JOIN patients p ON a.patient_id = p.patient_id
    INNER JOIN doctors d ON a.doctor_id = d.doctor_id;
    """
    response = client.post(
        "/api/admin/execute-query",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"query": query}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "columns" in data
    assert "rows" in data
    assert len(data["columns"]) >= 5

def test_sql_injection_rejection():
    adm_token = get_auth_token("admin@hospital.com", "Admin@123")
    # Disallow destructive/non-SELECT queries in demonstrator
    bad_query = "DROP TABLE users;"
    response = client.post(
        "/api/admin/execute-query",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"query": bad_query}
    )
    assert response.status_code == 400
