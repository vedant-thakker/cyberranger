import pytest
import os
from app.storage.database import Database
from app.review.triage import TriageQueue
from app.regression.archive import RegressionArchive
from app.security.target_client import DVWATargetClient
from app.experiments.referee import RefereeEngine


@pytest.fixture
def test_db(tmp_path):
    db_file = str(tmp_path / "test_cyberranger.db")
    return Database(db_file)


def test_database_crud(test_db):
    test_db.create_experiment("exp-1", "Test Run", total_rounds=10, seed=42)
    
    # Insert round
    round_id = test_db.insert_round({
        "experiment_id": "exp-1",
        "round_number": 1,
        "category": "sqli",
        "injection_point": "id_param",
        "strategy": "grammar_mutation",
        "transformations": ["none"],
        "payload": "1' OR '1'='1",
        "status_code": 200,
        "duration_ms": 12.5,
        "target_compromised": True,
        "detector_outcome": "Blocked",
        "rule_fired": "RULE-SQL-01",
        "ml_confidence": 0.0,
        "one_line_reason": "Blocked by rule",
        "novelty_reward": 1.0,
        "fitness_score": 0.8,
    })
    assert round_id > 0
    
    rounds = test_db.get_rounds("exp-1")
    assert len(rounds) == 1
    assert rounds[0]["payload"] == "1' OR '1'='1"
    assert rounds[0]["target_compromised"] == 1


def test_triage_queue_review_workflow(test_db):
    triage = TriageQueue(test_db)
    
    # Enqueue finding
    t_id = triage.enqueue(
        exp_id="exp-1",
        round_number=1,
        category="xss",
        payload="<script>alert(1)</script>",
        detector_verdict="Blocked",
        target_evidence="Reflected script",
    )
    assert t_id > 0
    
    # Verify pending
    pending = triage.get_pending("exp-1")
    assert len(pending) == 1
    assert pending[0]["human_status"] == "Pending"
    
    # Confirm finding
    triage.review_item(t_id, decision="Confirmed", note="Valid educational reflected XSS")
    
    # Verify confirmed samples extraction
    confirmed = triage.get_confirmed_training_samples("exp-1")
    assert len(confirmed) == 1
    assert confirmed[0] == ("<script>alert(1)</script>", 1)
    
    # Verify pending is now empty
    assert len(triage.get_pending("exp-1")) == 0


def test_referee_engine_round_execution(test_db):
    client = DVWATargetClient(base_url="http://127.0.0.1:8080")
    referee = RefereeEngine(
        exp_id="exp-integration",
        target_client=client,
        db=test_db,
        seed=42,
        cadence_rounds=2,
    )
    
    # Run round 1
    result1 = referee.run_round()
    assert result1["round_number"] == 1
    assert result1["category"] in RefereeEngine.CATEGORIES
    assert result1["status_code"] in [200, 302]
    assert len(result1["payload"]) > 0
    assert result1["detector_outcome"] in ["Clean", "Blocked", "Evaded"]
    
    # Run round 2 (should trigger retrain check at round 2)
    result2 = referee.run_round()
    assert result2["round_number"] == 2
    
    # Verify persisted in SQLite
    persisted_rounds = test_db.get_rounds("exp-integration")
    assert len(persisted_rounds) == 2
