def test_data_quality_detection_and_remediation(client):
    # 1. Run live scan
    scan_res = client.post("/api/data-quality/scan")
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["scanned_rules_count"] >= 5
    assert scan_data["open_issues_total"] >= 1

    # 2. List issues
    issues_res = client.get("/api/data-quality/issues?status=OPEN")
    assert issues_res.status_code == 200
    items = issues_res.json()["items"]
    assert len(items) > 0
    target_issue = items[0]
    issue_id = target_issue["issue_id"]

    # 3. Resolve the issue with controlled remediation notes
    resolve_res = client.post(f"/api/data-quality/issues/{issue_id}/resolve", json={
        "resolved_by": "QA-Lead-David",
        "resolution_status": "RESOLVED",
        "remediation_notes": "Root cause identified as network timeout during kiosk write. Manually verified arrival time."
    })
    assert resolve_res.status_code == 200
    resolved_data = resolve_res.json()
    assert resolved_data["resolution_status"] == "RESOLVED"
    assert resolved_data["resolved_by"] == "QA-Lead-David"
    assert "Root cause" in resolved_data["remediation_notes"]

    # 4. Attempting to re-resolve must fail
    re_resolve = client.post(f"/api/data-quality/issues/{issue_id}/resolve", json={
        "resolved_by": "QA-Lead-David",
        "resolution_status": "RESOLVED",
        "remediation_notes": "Trying again"
    })
    assert re_resolve.status_code == 409
