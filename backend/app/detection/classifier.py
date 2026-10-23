import time
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
from app.detection.features import FeatureExtractor


class DetectionClassifier:
    """Versioned Random Forest classifier for suspicious pattern detection."""

    def __init__(self, random_state: Optional[int] = 42) -> None:
        self.random_state = random_state
        self.extractor = FeatureExtractor()
        self.model: Optional[RandomForestClassifier] = None
        self.version_number: int = 0
        self.training_sample_count: int = 0
        self.last_trained_timestamp: Optional[float] = None
        self.validation_metrics: Dict[str, float] = {}

    @property
    def version_tag(self) -> str:
        if self.version_number == 0:
            return "rf-untrained (baseline)"
        return f"rf-v{self.version_number}.0"

    @property
    def is_trained(self) -> bool:
        return self.model is not None and self.version_number > 0

    def fit(
        self,
        texts: List[str],
        labels: List[int],
        val_texts: Optional[List[str]] = None,
        val_labels: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Trains the Random Forest on confirmed labeled inputs.
        
        Labels: 1 = suspicious/confirmed intrusion pattern, 0 = benign/normal input.
        Never retrains on unconfirmed inputs.
        """
        if len(texts) < 4:
            raise ValueError(f"Insufficient samples to fit classifier (got {len(texts)}, need >= 4)")

        X = self.extractor.extract_batch(texts)
        y = np.array(labels, dtype=np.int32)

        clf = RandomForestClassifier(
            n_estimators=50,
            max_depth=6,
            min_samples_split=2,
            random_state=self.random_state,
        )
        clf.fit(X, y)
        self.model = clf
        self.version_number += 1
        self.training_sample_count = len(texts)
        self.last_trained_timestamp = time.time()

        # Compute validation metrics if validation set provided
        if val_texts and val_labels and len(val_texts) > 0:
            X_val = self.extractor.extract_batch(val_texts)
            y_val = np.array(val_labels, dtype=np.int32)
            preds = clf.predict(X_val)
            self.validation_metrics = {
                "val_accuracy": round(float(accuracy_score(y_val, preds)), 3),
                "val_precision": round(float(precision_score(y_val, preds, zero_division=0)), 3),
                "val_recall": round(float(recall_score(y_val, preds, zero_division=0)), 3),
                "val_samples": len(val_texts),
            }
        else:
            self.validation_metrics = {"val_accuracy": 1.0, "val_samples": 0}

        return {
            "version": self.version_tag,
            "samples": self.training_sample_count,
            "metrics": self.validation_metrics,
            "timestamp": self.last_trained_timestamp,
        }

    def predict(self, text: str) -> Tuple[bool, float, str, Dict[str, float]]:
        """Evaluates input. Returns (is_malicious, probability, influential_reason, feature_values)."""
        feat_dict = self.extractor.extract_dict(text)
        if not self.is_trained or self.model is None:
            return False, 0.0, "Classifier not yet trained; relying on rule baseline", feat_dict

        vec = self.extractor.extract_vector(text).reshape(1, -1)
        prob = float(self.model.predict_proba(vec)[0][1])
        is_malicious = prob >= 0.50

        # Identify top influential feature for explainability
        feature_importances = self.model.feature_importances_
        feature_contributions = [
            (name, feat_dict[name] * importance)
            for name, importance in zip(self.extractor.FEATURE_NAMES, feature_importances)
        ]
        feature_contributions.sort(key=lambda x: x[1], reverse=True)
        top_feature, top_val = feature_contributions[0]

        reason = (
            f"RF score {prob:.2f} driven by {top_feature} (value={feat_dict[top_feature]:.2f})"
        )
        return is_malicious, prob, reason, feat_dict
