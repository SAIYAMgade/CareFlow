def test_encounter_workflow_and_pending_orders_rule(client):
    # 1. Create a clean encounter
    enc_payload = {
        "patient_id": 3,
        "encounter_type": "OUTPATIENT",
        "department": "Family Medicine",
        "provider_name": "Dr. James Wilson, MD",
        "chief_complaint": "Persistent fatigue and headaches"
    }
    enc_res = client.post("/api/encounters", json=enc_payload)
    assert enc_res.status_code == 201
    enc_id = enc_res.json()["encounter_id"]
    assert enc_res.json()["status"] == "OPEN"

    # 2. Place a clinical order for this encounter
    ord_payload = {
        "encounter_id": enc_id,
        "patient_id": 3,
        "order_type": "LABORATORY",
        "order_code": "CBC",
        "order_name": "Complete Blood Count",
        "priority": "ROUTINE",
        "ordered_by": "Dr. James Wilson, MD"
    }
    ord_res = client.post("/api/orders", json=ord_payload)
    assert ord_res.status_code == 201
    ord_id = ord_res.json()["order_id"]

    # 3. WORKFLOW SAFETY TEST: Try to complete encounter while order is still pending
    # This MUST be rejected by the backend business rule!
    compl_res = client.put(f"/api/encounters/{enc_id}/status", json={
        "new_status": "COMPLETED",
        "actor": "Dr. James Wilson, MD"
    })
    assert compl_res.status_code == 409
    assert "pending" in compl_res.json()["message"].lower()

    # 4. Complete the order with a result
    res_payload = {
        "result_value": "6.8",
        "reference_range": "4.5-11.0",
        "unit": "10^3/uL",
        "abnormal_flag": "NORMAL",
        "actor": "Lab-Tech-John"
    }
    ord_compl_res = client.post(f"/api/orders/{ord_id}/complete", json=res_payload)
    assert ord_compl_res.status_code == 200

    # 5. Now that all orders are completed, completing the encounter MUST succeed
    valid_compl = client.put(f"/api/encounters/{enc_id}/status", json={
        "new_status": "COMPLETED",
        "actor": "Dr. James Wilson, MD",
        "clinical_notes": "CBC within normal limits. Patient advised on sleep hygiene."
    })
    assert valid_compl.status_code == 200
    assert valid_compl.json()["status"] == "COMPLETED"
    assert valid_compl.json()["end_time"] is not None
