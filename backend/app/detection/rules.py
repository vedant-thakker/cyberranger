import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class RuleMatch:
    """Outcome of a triggered heuristic rule."""
    rule_id: str
    category: str
    matched_text: str
    reason: str
    severity: str


class RuleEngine:
    """Deterministic signature and structural heuristic rule engine."""

    VERSION = "rules-v1.4"

    def __init__(self) -> None:
        self.rules = [
            # SQL Injection Rules
            {
                "id": "RULE-SQL-01",
                "category": "sqli",
                "pattern": re.compile(r"(\bor\b|\band\b|\|\|)\s+(['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?|1\s*=\s*1)", re.IGNORECASE),
                "reason": "Tautological boolean injection pattern detected (OR/AND 1=1)",
                "severity": "high",
            },
            {
                "id": "RULE-SQL-02",
                "category": "sqli",
                "pattern": re.compile(r"\bunion\s+(all\s+)?select\b", re.IGNORECASE),
                "reason": "UNION SELECT query stacking pattern identified",
                "severity": "high",
            },
            {
                "id": "RULE-SQL-03",
                "category": "sqli",
                "pattern": re.compile(r"(['\"][^'\"]*(--|#|/\*))", re.IGNORECASE),
                "reason": "SQL comment terminator attached to quotation boundary",
                "severity": "medium",
            },
            # Cross-Site Scripting Rules
            {
                "id": "RULE-XSS-01",
                "category": "xss",
                "pattern": re.compile(r"<\s*script[^>]*>.*?(<\s*/\s*script\s*>)?", re.IGNORECASE | re.DOTALL),
                "reason": "Explicit HTML <script> tag detected in input parameter",
                "severity": "high",
            },
            {
                "id": "RULE-XSS-02",
                "category": "xss",
                "pattern": re.compile(r"<\s*\w+\s+[^>]*\bon(error|load|focus|mouseover|click)\s*=", re.IGNORECASE),
                "reason": "HTML tag embedding inline JavaScript event handler (e.g. onerror/onload)",
                "severity": "high",
            },
            {
                "id": "RULE-XSS-03",
                "category": "xss",
                "pattern": re.compile(r"javascript:\s*\w+\(", re.IGNORECASE),
                "reason": "JavaScript pseudo-protocol execution detected",
                "severity": "high",
            },
            # Command Injection Rules
            {
                "id": "RULE-CMD-01",
                "category": "cmdi",
                "pattern": re.compile(r"(&&|\|\||;|`|\$\()\s*(echo|cat|id|whoami|uname|sleep|ping)\b", re.IGNORECASE),
                "reason": "Shell command chaining operator attached to standard utility command",
                "severity": "critical",
            },
            {
                "id": "RULE-CMD-02",
                "category": "cmdi",
                "pattern": re.compile(r";\s*echo\s+CR_TEST_PING", re.IGNORECASE),
                "reason": "Known probe test string injected via command separator",
                "severity": "high",
            },
            # Path Traversal Rules
            {
                "id": "RULE-TRAV-01",
                "category": "path_traversal",
                "pattern": re.compile(r"(\.\./|\.\.\\|\.\.%2f|\.\.%5c){2,}", re.IGNORECASE),
                "reason": "Multiple sequential directory traversal sequences (../) found",
                "severity": "high",
            },
            {
                "id": "RULE-TRAV-02",
                "category": "path_traversal",
                "pattern": re.compile(r"(etc/passwd|windows/win\.ini|etc/hosts)", re.IGNORECASE),
                "reason": "Known sensitive operating system configuration file targeted",
                "severity": "high",
            },
            # Evasion Indicators
            {
                "id": "RULE-EVAS-01",
                "category": "evasion",
                "pattern": re.compile(r"%00|\x00", re.IGNORECASE),
                "reason": "Null-byte file extension or termination bypass character detected",
                "severity": "medium",
            },
            {
                "id": "RULE-EVAS-02",
                "category": "evasion",
                "pattern": re.compile(r"/\*!\d{5}.*?\*/|/\*\*\/", re.IGNORECASE),
                "reason": "Inline comment token fragmentation (/**/ or MySQL version comments) found",
                "severity": "medium",
            },
        ]

    def evaluate(self, text: str) -> Optional[RuleMatch]:
        """Evaluates text against the rule library. Returns first matching RuleMatch or None."""
        if not text:
            return None

        # Normalize URL-encoded characters for inspection
        normalized = text.replace("+", " ")

        for rule in self.rules:
            match = rule["pattern"].search(normalized)
            if match:
                return RuleMatch(
                    rule_id=rule["id"],
                    category=rule["category"],
                    matched_text=match.group(0),
                    reason=rule["reason"],
                    severity=rule["severity"],
                )
        return None
