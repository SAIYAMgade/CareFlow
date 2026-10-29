def test_list_patients(client):
    response = client.get("/api/patients?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 50
    assert len(data["items"]) == 10
    assert "mrn" in data["items"][0]

def test_register_patient_success(client):
    payload = {
        "first_name": "TestFirst",
        "last_name": "TestLast",
        "date_of_birth": "1990-05-15",
        "gender": "FEMALE",
        "phone": "555-9988",
        "email": "test.patient@example.com",
        "address": "456 Test Ave"
    }
    response = client.post("/api/patients", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["first_name"] == "TestFirst"
    assert created["last_name"] == "TestLast"
    assert created["mrn"].startswith("MRN-")
    assert created["status"] == "ACTIVE"

def test_register_patient_duplicate_mrn_rejected(client):
    payload1 = {
        "mrn": "MRN-DUP-TEST-001",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1985-01-01",
        "gender": "MALE"
    }
    res1 = client.post("/api/patients", json=payload1)
    assert res1.status_code == 201

    # Attempt duplicate registration with same MRN
    res2 = client.post("/api/patients", json=payload1)
    assert res2.status_code == 400
    err = res2.json()
    assert err["error"] is True
    assert "already exists" in err["message"]
