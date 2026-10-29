def test_create_and_check_in_appointment(client):
    # 1. Create a new appointment
    payload = {
        "patient_id": 1,
        "appointment_time": "2026-10-30T10:00:00",
        "appointment_type": "FOLLOW_UP",
        "department": "Cardiology",
        "provider_name": "Dr. Elena Rostova, MD"
    }
    create_res = client.post("/api/appointments", json=payload)
    assert create_res.status_code == 201
    appt = create_res.json()
    appt_id = appt["appointment_id"]
    assert appt["status"] == "SCHEDULED"

    # 2. Check in the appointment
    check_in_res = client.post(f"/api/appointments/{appt_id}/check-in", json={"actor": "Kiosk-01"})
    assert check_in_res.status_code == 200
    ci_data = check_in_res.json()
    assert ci_data["status"] == "CHECKED_IN"
    assert "encounter_id" in ci_data
    assert ci_data["encounter_id"] > 0

    # 3. Verify state transition rejection: Cannot check in an already CHECKED_IN appointment
    invalid_ci = client.post(f"/api/appointments/{appt_id}/check-in", json={"actor": "Kiosk-01"})
    assert invalid_ci.status_code == 409
    assert invalid_ci.json()["code"] == "INVALID_STATE_TRANSITION"

def test_cancel_appointment_workflow(client):
    payload = {
        "patient_id": 2,
        "appointment_time": "2026-10-31T14:00:00",
        "appointment_type": "INITIAL_CONSULT",
        "department": "Endocrinology",
        "provider_name": "Dr. Sarah Chen, MD"
    }
    create_res = client.post("/api/appointments", json=payload)
    appt_id = create_res.json()["appointment_id"]

    cancel_res = client.post(f"/api/appointments/{appt_id}/cancel", json={
        "cancel_reason": "Patient conflict with travel",
        "actor": "Staff-Sarah"
    })
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"
    assert cancel_res.json()["cancel_reason"] == "Patient conflict with travel"

    # Attempting to check in a cancelled appointment must be rejected
    checkin_cancelled = client.post(f"/api/appointments/{appt_id}/check-in", json={"actor": "FrontDesk"})
    assert checkin_cancelled.status_code == 409
