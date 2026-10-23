import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert "target_healthy" in data


def test_experiment_lifecycle_and_step():
    # 1. Start experiment
    start_resp = client.post(
        "/api/experiments/start",
        json={"name": "API Test", "total_rounds": 5, "seed": 42},
    )
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    exp_id = start_data["experiment_id"]
    assert len(exp_id) > 0
    
    # 2. Step 1 round
    step_resp = client.post(f"/api/experiments/{exp_id}/step")
    assert step_resp.status_code == 200
    round_data = step_resp.json()
    assert round_data["round_number"] == 1
    assert "detector_outcome" in round_data
    
    # 3. Fetch stats
    stats_resp = client.get(f"/api/experiments/{exp_id}/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["current_round"] == 1
    assert "detection_rate" in stats
    assert "archive_coverage" in stats
    
    # 4. Fetch rounds
    rounds_resp = client.get(f"/api/experiments/{exp_id}/rounds")
    assert rounds_resp.status_code == 200
    rounds = rounds_resp.json()
    assert len(rounds) == 1


def test_triage_api_workflow():
    # Query pending reviews
    pending_resp = client.get("/api/triage/pending")
    assert pending_resp.status_code == 200
    items = pending_resp.json()
    
    if len(items) > 0:
        item_id = items[0]["id"]
        # Submit review
        rev_resp = client.post(
            f"/api/triage/{item_id}/review",
            json={"decision": "Confirmed", "note": "Verified by test"},
        )
        assert rev_resp.status_code == 200
        assert "Confirmed" in rev_resp.json()["message"]


def test_export_endpoint():
    # Start experiment and step
    start_resp = client.post(
        "/api/experiments/start",
        json={"name": "Export Test", "total_rounds": 2, "seed": 99},
    )
    exp_id = start_resp.json()["experiment_id"]
    client.post(f"/api/experiments/{exp_id}/step")
    
    export_resp = client.get(f"/api/experiments/{exp_id}/export")
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["experiment_id"] == exp_id
    assert export_data["rounds_count"] >= 1
