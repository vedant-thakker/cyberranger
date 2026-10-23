from dataclasses import dataclass
from typing import Optional, Dict, Any
from app.detection.rules import RuleEngine, RuleMatch
from app.detection.classifier import DetectionClassifier


@dataclass
class DetectionVerdict:
    """Consolidated explainable verdict produced by the Detection Agent."""
    is_detected: bool
    verdict_label: str  # "Clean", "Blocked", "Evaded", "Unknown"
    rule_fired: Optional[str]
    rule_reason: Optional[str]
    ml_confidence: float
    ml_fired: bool
    ml_reason: str
    one_line_summary: str
    detector_version: str


class DetectionAgent:
    """Hybrid detection agent combining heuristic rules with a retrainable Random Forest."""

    def __init__(self, classifier: Optional[DetectionClassifier] = None) -> None:
        self.rule_engine = RuleEngine()
        self.classifier = classifier or DetectionClassifier()

    @property
    def version_tag(self) -> str:
        return f"{self.rule_engine.VERSION}+{self.classifier.version_tag}"

    def evaluate(self, input_text: str, target_compromised: bool) -> DetectionVerdict:
        """Evaluates a test case and forms a complete explainable verdict.
        
        Independent signals:
        - target_compromised: whether DVWA exhibited vulnerable behavior (ground truth of execution)
        - is_detected: whether rule engine OR classifier flagged the input as suspicious
        
        Verdict labeling:
        - If input is NOT suspicious and target was NOT compromised: "Clean"
        - If input was flagged by detector: "Blocked" (detector caught the pattern)
        - If target was compromised AND detector failed to flag: "Evaded" (generator bypassed detector)
        """
        rule_match: Optional[RuleMatch] = self.rule_engine.evaluate(input_text)
        ml_fired, ml_prob, ml_reason, _ = self.classifier.predict(input_text)

        is_detected = (rule_match is not None) or ml_fired

        if is_detected:
            verdict_label = "Blocked"
            if rule_match:
                summary = f"Blocked by {rule_match.rule_id}: {rule_match.reason}"
            else:
                summary = f"Blocked by ML ({self.classifier.version_tag}): {ml_reason}"
        else:
            if target_compromised:
                verdict_label = "Evaded"
                summary = f"Evaded detection: executed on target without triggering rules or ML threshold"
            else:
                verdict_label = "Clean"
                summary = "Clean: No suspicious heuristics triggered; target remained uncompromised"

        return DetectionVerdict(
            is_detected=is_detected,
            verdict_label=verdict_label,
            rule_fired=rule_match.rule_id if rule_match else None,
            rule_reason=rule_match.reason if rule_match else None,
            ml_confidence=round(ml_prob, 3),
            ml_fired=ml_fired,
            ml_reason=ml_reason,
            one_line_summary=summary,
            detector_version=self.version_tag,
        )
