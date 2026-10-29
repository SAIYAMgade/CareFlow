def test_order_result_review_lifecycle(client):
    # 1. Place a STAT lab order
    ord_payload = {
        "encounter_id": 1,
        "patient_id": 1,
        "order_type": "LABORATORY",
        "order_code": "BMP",
        "order_name": "Basic Metabolic Panel",
        "priority": "STAT",
        "ordered_by": "Dr. Elena Rostova, MD"
    }
    ord_res = client.post("/api/orders", json=ord_payload)
    assert ord_res.status_code == 201
    order_id = ord_res.json()["order_id"]
    assert ord_res.json()["order_status"] == "ORDERED"

    # 2. Lab technician posts result
    res_payload = {
        "result_value": "135",
        "reference_range": "70-99",
        "unit": "mg/dL",
        "abnormal_flag": "HIGH",
        "actor": "Lab-Tech-Sarah"
    }
    post_res = client.post(f"/api/orders/{order_id}/complete", json=res_payload)
    assert post_res.status_code == 200
    res_data = post_res.json()
    result_id = res_data["result_id"]
    assert res_data["result_status"] == "PENDING_REVIEW"
    assert res_data["abnormal_flag"] == "HIGH"

    # Verify order is now COMPLETED
    get_ord = client.get(f"/api/orders/{order_id}")
    assert get_ord.json()["order_status"] == "COMPLETED"

    # Attempting to post a duplicate result to the same order must fail
    dup_res = client.post(f"/api/orders/{order_id}/complete", json=res_payload)
    assert dup_res.status_code == 409

    # 3. Attending clinician reviews result
    review_res = client.post(f"/api/results/{result_id}/review", json={
        "reviewer": "Dr. Elena Rostova, MD"
    })
    assert review_res.status_code == 200
    assert review_res.json()["result_status"] == "REVIEWED"
    assert review_res.json()["reviewed_by"] == "Dr. Elena Rostova, MD"

    # Re-reviewing already reviewed result must fail
    re_review = client.post(f"/api/results/{result_id}/review", json={
        "reviewer": "Dr. Elena Rostova, MD"
    })
    assert re_review.status_code == 409
