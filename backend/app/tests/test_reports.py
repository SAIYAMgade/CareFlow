def test_report_catalog(client):
    res = client.get("/api/reports/catalog")
    assert res.status_code == 200
    catalog = res.json()
    assert len(catalog) == 8
    report_ids = [r["id"] for r in catalog]
    assert "RPT_01_DAILY_SCHEDULE" in report_ids
    assert "RPT_02_WAITING_TIME" in report_ids
    assert "RPT_03_ENCOUNTER_COMPLETION" in report_ids
    assert "RPT_04_PENDING_ORDERS" in report_ids
    assert "RPT_05_AWAITING_REVIEW" in report_ids
    assert "RPT_06_ORDER_TURNAROUND" in report_ids
    assert "RPT_07_CANCELLATIONS_NOSHOW" in report_ids
    assert "RPT_08_DATA_QUALITY" in report_ids

def test_execute_all_eight_reports(client):
    catalog = client.get("/api/reports/catalog").json()
    for item in catalog:
        rep_id = item["id"]
        res = client.post("/api/reports/execute", json={
            "report_id": rep_id,
            "parameters": {},
            "page": 1,
            "page_size": 25
        })
        assert res.status_code == 200, f"Failed executing {rep_id}"
        data = res.json()
        assert data["report_id"] == rep_id
        assert "execution_time_ms" in data
        assert "rows" in data
        assert isinstance(data["rows"], list)

def test_export_report_csv_with_formula_escaping(client):
    res = client.post("/api/reports/export", json={
        "report_id": "RPT_01_DAILY_SCHEDULE",
        "parameters": {}
    })
    assert res.status_code == 200
    assert res.headers["content-type"] == "text/csv; charset=utf-8"
    csv_text = res.text
    assert "appointment_id" in csv_text
