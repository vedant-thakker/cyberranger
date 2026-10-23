import pytest
from app.detection.rules import RuleEngine
from app.detection.features import FeatureExtractor
from app.detection.classifier import DetectionClassifier
from app.detection.agent import DetectionAgent
from app.detection.retrain import RetrainCadenceController


def test_rule_engine_matching():
    engine = RuleEngine()
    
    # SQLi match
    m_sql = engine.evaluate("admin' OR 1=1 --")
    assert m_sql is not None
    assert m_sql.category == "sqli"
    assert "RULE-SQL" in m_sql.rule_id
    
    # XSS match
    m_xss = engine.evaluate("<script>alert(1)</script>")
    assert m_xss is not None
    assert m_xss.category == "xss"
    
    # CMDi match
    m_cmd = engine.evaluate("127.0.0.1; echo CR_TEST_PING")
    assert m_cmd is not None
    assert m_cmd.category == "cmdi"
    
    # Path Traversal match
    m_trav = engine.evaluate("../../../../etc/passwd")
    assert m_trav is not None
    assert m_trav.category == "path_traversal"
    
    # Benign text
    m_clean = engine.evaluate("John Doe")
    assert m_clean is None


def test_feature_extractor_dimensions_and_entropy():
    extractor = FeatureExtractor()
    sample = "<script>alert('test')</script>"
    
    feats = extractor.extract_dict(sample)
    assert len(feats) == len(FeatureExtractor.FEATURE_NAMES)
    assert feats["input_length"] == len(sample)
    assert feats["shannon_entropy"] > 0.0
    assert feats["xss_tag_score"] >= 1.0
    
    vec = extractor.extract_vector(sample)
    assert vec.shape == (14,)


def test_classifier_untrained_baseline():
    classifier = DetectionClassifier()
    assert classifier.is_trained is False
    assert classifier.version_tag == "rf-untrained (baseline)"
    
    is_mal, prob, reason, _ = classifier.predict("SELECT * FROM users")
    assert is_mal is False
    assert prob == 0.0
    assert "baseline" in reason.lower()


def test_retrain_cadence_and_versioning():
    classifier = DetectionClassifier(random_state=42)
    controller = RetrainCadenceController(classifier, cadence_rounds=5, min_confirmed_samples=4)
    
    # Check cadence trigger
    assert controller.should_check_retrain(4) is False
    assert controller.should_check_retrain(5) is True
    assert controller.should_check_retrain(10) is True
    
    # Retrain with educational baseline
    event = controller.retrain_from_confirmed(
        confirmed_samples=[
            ("1' UNION SELECT null, 1 #", 1),
            ("profile_id_99", 0),
        ],
        current_round=5,
        include_baseline=True,
    )
    assert event is not None
    assert classifier.is_trained is True
    assert classifier.version_tag == "rf-v1.0"
    assert "val_accuracy" in event["validation_metrics"]
    
    # Predict with newly trained classifier
    is_mal, prob, reason, _ = classifier.predict("1' OR '1'='1")
    assert prob > 0.40  # Model recognized the pattern
    assert "rf score" in reason.lower()


def test_detection_agent_verdicts():
    agent = DetectionAgent()
    
    # Clean input, target uncompromised
    v1 = agent.evaluate("1", target_compromised=False)
    assert v1.verdict_label == "Clean"
    assert v1.is_detected is False
    
    # Attack caught by rule -> Blocked
    v2 = agent.evaluate("<script>alert(1)</script>", target_compromised=True)
    assert v2.verdict_label == "Blocked"
    assert v2.is_detected is True
    assert v2.rule_fired is not None
    
    # Target compromised, but not detected -> Evaded
    v3 = agent.evaluate("benign_looking_bypass", target_compromised=True)
    assert v3.verdict_label == "Evaded"
    assert v3.is_detected is False
