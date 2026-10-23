from typing import List, Tuple, Dict, Any, Optional
from app.storage.database import Database


class TriageQueue:
    """Human-in-the-loop triage queue.
    
    Ensures that only human-confirmed findings ever enter the blue detector training dataset.
    The system never self-certifies a finding.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    def enqueue(
        self,
        exp_id: str,
        round_number: int,
        category: str,
        payload: str,
        detector_verdict: str,
        target_evidence: str,
    ) -> int:
        """Adds a newly discovered candidate to the review queue."""
        return self.db.insert_triage_item(
            exp_id=exp_id,
            round_number=round_number,
            category=category,
            payload=payload,
            detector_verdict=detector_verdict,
            target_evidence=target_evidence,
        )

    def review_item(self, review_id: int, decision: str, note: Optional[str] = None) -> None:
        """Records a human reviewer's decision: Confirmed, Rejected, or Duplicate."""
        valid_decisions = {"Confirmed", "Rejected", "Duplicate"}
        if decision not in valid_decisions:
            raise ValueError(f"Invalid decision '{decision}'. Must be one of {valid_decisions}")
        self.db.update_triage_status(review_id, status=decision, note=note)

    def get_pending(self, exp_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all unreviewed items."""
        items = self.db.get_triage_items(exp_id)
        return [i for i in items if i["human_status"] == "Pending"]

    def get_confirmed_training_samples(self, exp_id: Optional[str] = None) -> List[Tuple[str, int]]:
        """Extracts strictly confirmed samples for blue agent model retraining.
        
        Returns List of (payload, label), where 1 = confirmed intrusion pattern.
        """
        items = self.db.get_triage_items(exp_id)
        confirmed = []
        for item in items:
            if item["human_status"] == "Confirmed":
                # Confirmed attack structure
                confirmed.append((item["payload"], 1))
        return confirmed
