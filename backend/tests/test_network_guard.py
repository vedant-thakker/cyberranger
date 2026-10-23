import pytest
from app.security.network_guard import NetworkGuard, SecurityBoundaryViolation


def test_network_guard_allows_local_dvwa_endpoints():
    guard = NetworkGuard(target_host="127.0.0.1", target_port=8080)
    
    # Authorized endpoints on 127.0.0.1:8080
    valid_urls = [
        "http://127.0.0.1:8080/login.php",
        "http://127.0.0.1:8080/vulnerabilities/sqli/?id=1&Submit=Submit",
        "http://127.0.0.1:8080/vulnerabilities/xss_r/?name=test",
        "http://127.0.0.1:8080/vulnerabilities/exec/",
        "http://127.0.0.1:8080/vulnerabilities/fi/?page=include.php",
        "http://localhost:8080/vulnerabilities/sqli/",
    ]
    for url in valid_urls:
        guard.validate_destination(url)  # Should not raise


def test_network_guard_blocks_external_domains():
    guard = NetworkGuard()
    
    external_domains = [
        "http://example.com/login.php",
        "http://google.com/",
        "http://142.250.190.46:8080/test",
        "https://github.com",
        "http://attacker.local:8080/vulnerabilities/sqli/",
    ]
    for url in external_domains:
        with pytest.raises(SecurityBoundaryViolation) as exc_info:
            guard.validate_destination(url)
        msg = str(exc_info.value).lower()
        assert "rejected" in msg or "non-local" in msg or "unauthorized" in msg


def test_network_guard_blocks_unauthorized_ports():
    guard = NetworkGuard(target_port=8080)
    
    # Same loopback, wrong port
    invalid_ports = [
        "http://127.0.0.1:80/login.php",
        "http://127.0.0.1:443/",
        "http://127.0.0.1:22/test",
        "http://127.0.0.1:9000/vulnerabilities/sqli/",
    ]
    for url in invalid_ports:
        with pytest.raises(SecurityBoundaryViolation) as exc_info:
            guard.validate_destination(url)
        assert "port" in str(exc_info.value).lower()


def test_network_guard_blocks_unauthorized_endpoints():
    guard = NetworkGuard()
    
    # Loopback port 8080, but unauthorized path
    invalid_paths = [
        "http://127.0.0.1:8080/admin/users",
        "http://127.0.0.1:8080/api/v1/keys",
        "http://127.0.0.1:8080/etc/shadow",
        "http://127.0.0.1:8080/wp-admin",
    ]
    for url in invalid_paths:
        with pytest.raises(SecurityBoundaryViolation) as exc_info:
            guard.validate_destination(url)
        assert "not within authorized" in str(exc_info.value).lower()


def test_network_guard_emergency_stop():
    guard = NetworkGuard()
    # Before stop, valid URL passes
    guard.validate_destination("http://127.0.0.1:8080/login.php")
    
    # Trigger emergency stop
    guard.trigger_emergency_stop()
    assert guard.is_stopped is True
    
    # Now all requests are blocked
    with pytest.raises(SecurityBoundaryViolation) as exc_info:
        guard.validate_destination("http://127.0.0.1:8080/login.php")
    assert "emergency stop active" in str(exc_info.value).lower()
    
    # After reset
    guard.reset_emergency_stop()
    assert guard.is_stopped is False
    guard.validate_destination("http://127.0.0.1:8080/login.php")


def test_network_guard_blocks_private_non_loopback_ips():
    guard = NetworkGuard()
    
    # RFC 1918 private addresses that are NOT loopback
    non_loopback = [
        "http://192.168.1.1:8080/vulnerabilities/sqli/",
        "http://10.0.0.1:8080/vulnerabilities/sqli/",
        "http://172.16.0.1:8080/vulnerabilities/sqli/",
    ]
    for url in non_loopback:
        with pytest.raises(SecurityBoundaryViolation) as exc_info:
            guard.validate_destination(url)
        assert "non-local" in str(exc_info.value).lower() or "rejected" in str(exc_info.value).lower()
