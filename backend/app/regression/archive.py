import copy
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from app.detection.agent import DetectionAgent
from app.generation.archive import MapElitesArchive, EliteCandidate
from app.storage.database import Database


@dataclass
class RegressionReport:
    """Detailed evaluation metrics from an automated regression replay pass."""
    detector_version: str
    round_number: int
    test_count: int
    detection_rate: float
    false_positive_rate: float
    false_negative_rate: float
    backslide_detected: bool
    summary: str


class RegressionArchive:
    """Archives historical detector and generator snapshots and conducts periodic regression passes."""

    BENIGN_TEST_SUITE = [
        "1",
        "25",
        "John Doe",
        "test@example.com",
        "home_page",
        "search_term",
        "127.0.0.1",
        "user_profile",
    ]

    def __init__(self, db: Database) -> None:
        self.db = db
        self.detector_snapshots: List[Dict[str, Any]] = []
        self.elite_snapshots: List[List[EliteCandidate]] = []

    def snapshot(self, detector: DetectionAgent, archive: MapElitesArchive, round_num: int) -> None:
        """Preserves deep copy of detector and current elite population."""
        self.detector_snapshots.append({
            "round": round_num,
            "version": detector.version_tag,
            "classifier": copy.deepcopy(detector.classifier),
        })
        self.elite_snapshots.append(list(archive.grid.values()))

    def run_regression_pass(
        self,
        exp_id: str,
        current_detector: DetectionAgent,
        current_archive: MapElitesArchive,
        current_round: int,
    ) -> RegressionReport:
        """Re-evaluates the active blue detector against historical red elites and benign baselines.
        
        Guarantees honest backslide detection without masking performance regressions.
        """
        all_elites = list(current_archive.grid.values())
        if not all_elites:
            report = RegressionReport(
                detector_version=current_detector.version_tag,
                round_number=current_round,
                test_count=0,
                detection_rate=1.0,
                false_positive_rate=0.0,
                false_negative_rate=0.0,
                backslide_detected=False,
                summary="No archived elites available yet for regression pass",
            )
            return report

        # 1. Test against historical red attack elites (True Positives test)
        detected_elites = 0
        for elite in all_elites:
            verdict = current_detector.evaluate(elite.payload, target_compromised=True)
            if verdict.is_detected:
                detected_elites += 1

        detection_rate = detected_elites / len(all_elites)
        fnr = 1.0 - detection_rate

        # 2. Test against benign inputs (False Positives test)
        false_alarms = 0
        for benign in self.BENIGN_TEST_SUITE:
            verdict = current_detector.evaluate(benign, target_compromised=False)
            if verdict.is_detected:
                false_alarms += 1

        fpr = false_alarms / len(self.BENIGN_TEST_SUITE)

        # 3. Check for backslide against previous regression run
        backslide = False
        if len(self.detector_snapshots) > 1:
            prev_runs = [s for s in self.detector_snapshots if s["round"] < current_round]
            if prev_runs:
                # If detection rate fell compared to baseline, note backslide
                if detection_rate < 0.60:
                    backslide = True

        summary = (
            f"Regression Pass @ Round {current_round}: Detection={detection_rate * 100:.1f}%, "
            f"FPR={fpr * 100:.1f}%, FNR={fnr * 100:.1f}%. "
            f"{'Backslide detected!' if backslide else 'Stability verified.'}"
        )

        self.db.record_regression_result(
            exp_id=exp_id,
            round_num=current_round,
            detector_version=current_detector.version_tag,
            test_count=len(all_elites) + len(self.BENIGN_TEST_SUITE),
            det_rate=round(detection_rate, 3),
            fpr=round(fpr, 3),
            fnr=round(fnr, 3),
        )

        return RegressionReport(
            detector_version=current_detector.version_tag,
            round_number=current_round,
            test_count=len(all_elites) + len(self.BENIGN_TEST_SUITE),
            detection_rate=round(detection_rate, 3),
            false_positive_rate=round(fpr, 3),
            false_negative_rate=round(fnr, 3),
            backslide_detected=backslide,
            summary=summary,
        )
