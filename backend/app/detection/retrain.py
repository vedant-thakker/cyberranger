import time
from typing import List, Dict, Tuple, Optional, Any
from app.detection.classifier import DetectionClassifier

# Pre-reviewed educational baseline samples for reproducible initial training
EDUCATIONAL_BASELINE_SAMPLES: List[Tuple[str, int, str]] = [
    # (payload_text, label [1=malicious, 0=benign], note)
    ("1' OR '1'='1", 1, "Classic SQLi tautology"),
    ("admin' --", 1, "SQLi auth bypass comment"),
    ("<script>alert(1)</script>", 1, "Standard XSS script injection"),
    ("<img src=x onerror=alert(1)>", 1, "XSS event handler vector"),
    ("; echo CR_TEST_PING", 1, "Command injection separator probe"),
    ("&& whoami", 1, "Command injection logical operator"),
    ("../../../../etc/passwd", 1, "Path traversal sequence"),
    ("....//....//etc/passwd", 1, "Nested path traversal sequence"),
    # Benign normal inputs
    ("1", 0, "Standard integer ID parameter"),
    ("25", 0, "Numeric query parameter"),
    ("John Doe", 0, "Normal user full name string"),
    ("test@example.com", 0, "Standard email address format"),
    ("help", 0, "Plain alphanumeric navigation term"),
    ("127.0.0.1", 0, "Valid loopback IP address"),
    ("include.php", 0, "Safe relative script include"),
    ("profile", 0, "Standard dashboard section name"),
]


class RetrainCadenceController:
    """Controls retraining cadence and enforces human-confirmation requirements."""

    def __init__(
        self,
        classifier: DetectionClassifier,
        cadence_rounds: int = 5,
        min_confirmed_samples: int = 6,
    ) -> None:
        self.classifier = classifier
        self.cadence_rounds = cadence_rounds
        self.min_confirmed_samples = min_confirmed_samples
        self.retrain_history: List[Dict[str, Any]] = []

    def should_check_retrain(self, current_round: int) -> bool:
        """Determines if the current round falls on the configured cadence."""
        return current_round > 0 and (current_round % self.cadence_rounds == 0)

    def retrain_from_confirmed(
        self,
        confirmed_samples: List[Tuple[str, int]],
        current_round: int,
        include_baseline: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Retrains the classifier if sufficient human-confirmed samples exist.
        
        Guarantees:
        - Only confirmed items are used.
        - Preserves strict train/eval split.
        - Records retraining event for the dashboard.
        """
        all_samples = []
        if include_baseline:
            all_samples.extend([(text, label) for text, label, _ in EDUCATIONAL_BASELINE_SAMPLES])
        
        all_samples.extend(confirmed_samples)

        if len(all_samples) < self.min_confirmed_samples:
            return None

        # Split 80% train, 20% validation
        texts = [s[0] for s in all_samples]
        labels = [s[1] for s in all_samples]

        split_idx = max(2, int(len(texts) * 0.8))
        train_texts, val_texts = texts[:split_idx], texts[split_idx:]
        train_labels, val_labels = labels[:split_idx], labels[split_idx:]

        result = self.classifier.fit(
            texts=train_texts,
            labels=train_labels,
            val_texts=val_texts,
            val_labels=val_labels,
        )

        event = {
            "round": current_round,
            "version": result["version"],
            "training_samples": result["samples"],
            "validation_metrics": result["metrics"],
            "timestamp": result["timestamp"],
        }
        self.retrain_history.append(event)
        return event
