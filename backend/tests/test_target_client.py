import pytest
from app.security.target_client import DVWATargetClient


def test_target_client_health_and_auth():
    client = DVWATargetClient(base_url="http://127.0.0.1:8080")
    # Verify health
    healthy = client.check_health()
    assert healthy is True, "DVWA container should be reachable and healthy on 127.0.0.1:8080"
    
    # Authenticate
    authenticated = client.authenticate()
    assert authenticated is True, "Should authenticate with DVWA successfully"


def test_target_client_sqli_execution():
    client = DVWATargetClient(base_url="http://127.0.0.1:8080")
    result = client.execute_test("sqli", "1' OR '1'='1")
    assert result.status_code == 200
    assert result.indicator_triggered is True
    assert "admin" in result.evidence_snippet.lower() or "records" in result.evidence_snippet.lower()


def test_target_client_xss_execution():
    client = DVWATargetClient(base_url="http://127.0.0.1:8080")
    result = client.execute_test("xss", "<script>alert(1)</script>")
    assert result.status_code == 200
    assert result.indicator_triggered is True


def test_target_client_cmdi_execution():
    client = DVWATargetClient(base_url="http://127.0.0.1:8080")
    result = client.execute_test("cmdi", "echo CR_TEST_PING")
    assert result.status_code == 200
    assert result.indicator_triggered is True


def test_target_client_path_traversal_execution():
    client = DVWATargetClient(base_url="http://127.0.0.1:8080")
    result = client.execute_test("path_traversal", "/etc/passwd")
    assert result.status_code == 200
    assert result.indicator_triggered is True
