import re
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
import requests

from app.security.network_guard import NetworkGuard, SecurityBoundaryViolation


@dataclass
class TargetExecutionResult:
    """Outcome of an isolated test execution against the local target."""
    category: str
    target_url: str
    status_code: int
    duration_ms: float
    indicator_triggered: bool
    evidence_snippet: str
    error: Optional[str] = None


class DVWATargetClient:
    """Authenticated HTTP client interacting exclusively with the local DVWA container."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        network_guard: Optional[NetworkGuard] = None,
        timeout_seconds: float = 4.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.guard = network_guard or NetworkGuard()
        self.timeout = timeout_seconds
        self.session = requests.Session()
        self.session.hooks["response"].append(self.guard.filter_redirect)
        self.is_authenticated = False

    def check_health(self) -> bool:
        """Verifies local DVWA reachability without performing security tests."""
        url = f"{self.base_url}/login.php"
        try:
            self.guard.validate_destination(url)
            resp = self.session.get(url, timeout=self.timeout)
            return resp.status_code == 200 and "Damn Vulnerable Web Application" in resp.text
        except Exception:
            return False

    def authenticate(self, username: str = "admin", password: str = "password") -> bool:
        """Logs into local DVWA and sets security level to 'low'."""
        login_url = f"{self.base_url}/login.php"
        setup_url = f"{self.base_url}/setup.php"
        sec_url = f"{self.base_url}/security.php"

        try:
            self.guard.validate_destination(login_url)
            self.guard.validate_destination(setup_url)
            self.guard.validate_destination(sec_url)

            # Check setup/database status
            setup_page = self.session.get(setup_url, timeout=self.timeout)
            token_match = re.search(r"name='user_token'\s+value='([^']+)'", setup_page.text)
            if token_match:
                token = token_match.group(1)
                self.session.post(
                    setup_url,
                    data={"create_db": "Create / Reset Database", "user_token": token},
                    timeout=self.timeout,
                )

            # Fetch login page token
            login_page = self.session.get(login_url, timeout=self.timeout)
            login_token_match = re.search(r"name='user_token'\s+value='([^']+)'", login_page.text)
            login_token = login_token_match.group(1) if login_token_match else ""

            login_data = {
                "username": username,
                "password": password,
                "Login": "Login",
            }
            if login_token:
                login_data["user_token"] = login_token

            resp = self.session.post(login_url, data=login_data, timeout=self.timeout)
            
            # Set security level to low
            self.session.post(
                sec_url,
                data={"security": "low", "seclev_submit": "Submit"},
                timeout=self.timeout,
            )
            self.session.cookies.set("security", "low")

            self.is_authenticated = True
            return True
        except Exception as e:
            self.is_authenticated = False
            return False

    def execute_test(self, category: str, payload: str) -> TargetExecutionResult:
        """Executes a laboratory test input against the designated category endpoint.
        
        Evaluates genuine response behavior to determine whether the practice target
        exhibited the category-specific indicator.
        """
        if not self.is_authenticated:
            self.authenticate()

        start_time = time.perf_counter()
        indicator_triggered = False
        evidence = ""
        status_code = 0

        try:
            if category == "sqli":
                endpoint = f"{self.base_url}/vulnerabilities/sqli/"
                url = f"{endpoint}?id={payload}&Submit=Submit"
                self.guard.validate_destination(url)
                resp = self.session.get(url, timeout=self.timeout)
                status_code = resp.status_code
                duration_ms = (time.perf_counter() - start_time) * 1000

                # DVWA SQLi indicators: Multiple records returned or database error
                if "First name: admin" in resp.text and "First name: Gordon" in resp.text:
                    indicator_triggered = True
                    evidence = "Multiple user records retrieved (admin + Gordon)"
                elif "You have an error in your SQL syntax" in resp.text:
                    indicator_triggered = True
                    evidence = "Database syntax exception revealed in response"
                else:
                    evidence = "Single or no record returned"

                return TargetExecutionResult(
                    category=category,
                    target_url=url,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    indicator_triggered=indicator_triggered,
                    evidence_snippet=evidence,
                )

            elif category == "xss":
                endpoint = f"{self.base_url}/vulnerabilities/xss_r/"
                url = f"{endpoint}?name={payload}#"
                self.guard.validate_destination(url)
                resp = self.session.get(url, timeout=self.timeout)
                status_code = resp.status_code
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Reflected XSS check: unescaped payload or script tag reflected
                cleaned_payload = payload.replace("+", " ")
                if "<script>" in resp.text or "<svg" in resp.text or "<img" in resp.text:
                    indicator_triggered = True
                    evidence = "Unescaped HTML/script tag reflected in body"
                elif cleaned_payload in resp.text and ("<" in cleaned_payload or ">" in cleaned_payload):
                    indicator_triggered = True
                    evidence = "Raw HTML payload reflected without sanitization"
                else:
                    evidence = "Payload encoded or not reflected"

                return TargetExecutionResult(
                    category=category,
                    target_url=url,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    indicator_triggered=indicator_triggered,
                    evidence_snippet=evidence,
                )

            elif category == "cmdi":
                endpoint = f"{self.base_url}/vulnerabilities/exec/"
                self.guard.validate_destination(endpoint)
                resp = self.session.post(
                    endpoint,
                    data={"ip": f"127.0.0.1 && {payload}", "Submit": "Submit"},
                    timeout=self.timeout,
                )
                status_code = resp.status_code
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Command injection indicators: output of injected commands (echo, id, whoami, uname)
                if any(ind in resp.text for ind in ["CR_TEST_PING", "uid=", "www-data", "Linux"]):
                    indicator_triggered = True
                    evidence = "Command execution indicator found in preformatted response"
                else:
                    evidence = "Standard ping response only"

                return TargetExecutionResult(
                    category=category,
                    target_url=endpoint,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    indicator_triggered=indicator_triggered,
                    evidence_snippet=evidence,
                )

            elif category == "path_traversal":
                endpoint = f"{self.base_url}/vulnerabilities/fi/"
                url = f"{endpoint}?page={payload}"
                self.guard.validate_destination(url)
                resp = self.session.get(url, timeout=self.timeout)
                status_code = resp.status_code
                duration_ms = (time.perf_counter() - start_time) * 1000

                # Path traversal indicators: /etc/passwd or php warning
                if "root:x:0:0" in resp.text or "bin/bash" in resp.text:
                    indicator_triggered = True
                    evidence = "Local system file structure contents disclosed"
                elif "failed to open stream: No such file or directory" in resp.text:
                    indicator_triggered = True
                    evidence = "File inclusion path traversal reached PHP file system handler"
                else:
                    evidence = "Default page included"

                return TargetExecutionResult(
                    category=category,
                    target_url=url,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    indicator_triggered=indicator_triggered,
                    evidence_snippet=evidence,
                )

            else:
                return TargetExecutionResult(
                    category=category,
                    target_url="",
                    status_code=400,
                    duration_ms=0.0,
                    indicator_triggered=False,
                    evidence_snippet="Unsupported category",
                    error=f"Unknown category '{category}'",
                )

        except SecurityBoundaryViolation as e:
            return TargetExecutionResult(
                category=category,
                target_url="",
                status_code=403,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                indicator_triggered=False,
                evidence_snippet="Blocked by NetworkGuard",
                error=str(e),
            )
        except Exception as e:
            return TargetExecutionResult(
                category=category,
                target_url="",
                status_code=500,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                indicator_triggered=False,
                evidence_snippet="Execution failed",
                error=str(e),
            )
