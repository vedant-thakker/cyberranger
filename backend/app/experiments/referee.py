import random
import time
from typing import Dict, List, Optional, Callable, Any
from app.generation.ast import GrammarNode
from app.generation.grammars import GrammarEngine
from app.generation.mutation import GrammarMutator
from app.generation.crossover import GeneticCrossover
from app.generation.transforms import TransformPipeline
from app.generation.archive import MapElitesArchive
from app.generation.bandit import UCB1Bandit
from app.generation.optional_llm import LLMStructureProposer
from app.security.target_client import DVWATargetClient
from app.detection.agent import DetectionAgent, DetectionVerdict
from app.detection.retrain import RetrainCadenceController
from app.review.triage import TriageQueue
from app.regression.archive import RegressionArchive
from app.storage.database import Database


class RefereeEngine:
    """Coordinates co-evolutionary experiment rounds between Generator and Detector agents."""

    CATEGORIES = ["sqli", "xss", "cmdi", "path_traversal"]
    INJECTION_POINTS = {
        "sqli": "id_param",
        "xss": "name_param",
        "cmdi": "ip_param",
        "path_traversal": "page_param",
    }

    def __init__(
        self,
        exp_id: str,
        target_client: DVWATargetClient,
        db: Database,
        seed: Optional[int] = 42,
        cadence_rounds: int = 5,
        enable_llm: bool = False,
    ) -> None:
        self.exp_id = exp_id
        self.target_client = target_client
        self.db = db
        self.seed = seed
        self.rng = random.Random(seed)

        # Core components
        self.grammar_engine = GrammarEngine(seed=seed)
        self.mutator = GrammarMutator(self.grammar_engine, seed=seed)
        self.crossover = GeneticCrossover(seed=seed)
        self.transforms = TransformPipeline(seed=seed)
        self.archive = MapElitesArchive()
        self.bandit = UCB1Bandit(seed=seed)
        self.llm_proposer = LLMStructureProposer(enabled=enable_llm)

        # Blue detection components
        self.detector = DetectionAgent()
        self.retrain_controller = RetrainCadenceController(self.detector.classifier, cadence_rounds=cadence_rounds)
        self.triage_queue = TriageQueue(db)
        self.regression = RegressionArchive(db)

        # Runtime control flags
        self.current_round = 0
        self.is_paused = False
        self.is_stopped = False
        self.event_callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def register_event_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribes an SSE or logging handler to completed round events."""
        self.event_callbacks.append(callback)

    def _broadcast_event(self, event_data: Dict[str, Any]) -> None:
        for cb in self.event_callbacks:
            try:
                cb(event_data)
            except Exception:
                pass

    def run_round(self) -> Dict[str, Any]:
        """Executes a single end-to-end co-evolutionary experiment round."""
        if self.is_stopped:
            return {"status": "stopped"}

        self.current_round += 1
        category = self.CATEGORIES[(self.current_round - 1) % len(self.CATEGORIES)]
        injection_point = self.INJECTION_POINTS[category]

        # 1. Select generation strategy via UCB1 Bandit
        has_crossover_candidates = len(self.archive.get_elites_by_category(category)) >= 2
        strategy = self.bandit.select_arm(has_crossover_candidates=has_crossover_candidates)

        # 2. Generate candidate test input
        tree: Optional[GrammarNode] = None
        payload: str = ""
        applied_transforms: List[str] = []
        strategy_note: str = ""

        if strategy == "grammar_mutation":
            base_tree = self.grammar_engine.expand(category)
            tree, strategy_note = self.mutator.mutate(base_tree, category)
            payload = tree.to_string()

        elif strategy == "genetic_crossover":
            elites = self.archive.get_elites_by_category(category)
            if len(elites) >= 2:
                parents = self.rng.sample(elites, 2)
                p1 = parents[0].tree or self.grammar_engine.expand(category)
                p2 = parents[1].tree or self.grammar_engine.expand(category)
                tree, strategy_note = self.crossover.crossover(p1, p2, category)
                payload = tree.to_string()
            else:
                tree = self.grammar_engine.expand(category)
                payload = tree.to_string()
                strategy_note = "Fallback to grammar expansion (insufficient crossover parents)"

        elif strategy == "combinatorial_transform":
            tree = self.grammar_engine.expand(category)
            raw_text = tree.to_string()
            payload, applied_transforms = self.transforms.apply_random_combination(raw_text, max_transforms=2)
            strategy_note = f"Applied transforms: {', '.join(applied_transforms)}"

        elif strategy == "structural_proposal":
            proposal = self.llm_proposer.propose(category)
            if proposal:
                tree = self.llm_proposer.render_to_grammar_tree(proposal, self.grammar_engine)
                payload = tree.to_string()
                strategy_note = f"Rendered structural pattern: {proposal.pattern_type}"
            else:
                tree = self.grammar_engine.expand(category)
                payload = tree.to_string()
                strategy_note = "Proposer disabled/unavailable; standard grammar fallback"

        # 3. Submit request to local DVWA container via NetworkGuard
        exec_result = self.target_client.execute_test(category, payload)
        target_compromised = exec_result.indicator_triggered

        # 4. Evaluate through Detection Agent
        verdict: DetectionVerdict = self.detector.evaluate(payload, target_compromised=target_compromised)

        # 5. Determine primary transform label for MAP-Elites
        primary_transform = applied_transforms[0] if applied_transforms else "none"

        # 6. Insert into MAP-Elites archive
        # Base fitness combination: target compromise (0.5), evasion (0.3), novelty (0.2)
        novelty_reward = 0.0
        fitness_score = (
            (0.5 if target_compromised else 0.1)
            + (0.3 if not verdict.is_detected else 0.0)
        )

        is_new_cell, novelty_reward, archive_msg = self.archive.insert(
            category=category,
            injection_point=injection_point,
            evasion_technique=primary_transform,
            detector_outcome=verdict.verdict_label.lower(),
            payload=payload,
            tree=tree,
            fitness_score=fitness_score,
            round_num=self.current_round,
        )

        # Combine novelty reward into final fitness
        total_fitness = fitness_score + (0.2 * novelty_reward)

        # 7. Update UCB1 bandit with measured reward
        self.bandit.update(strategy, reward=total_fitness)

        # 8. Human-in-the-loop review queue
        # Every new finding enters review; system never self-certifies
        triage_id = self.triage_queue.enqueue(
            exp_id=self.exp_id,
            round_number=self.current_round,
            category=category,
            payload=payload,
            detector_verdict=verdict.verdict_label,
            target_evidence=exec_result.evidence_snippet,
        )

        # 9. Retrain cadence check
        retrain_event = None
        if self.retrain_controller.should_check_retrain(self.current_round):
            confirmed_samples = self.triage_queue.get_confirmed_training_samples(self.exp_id)
            retrain_event = self.retrain_controller.retrain_from_confirmed(
                confirmed_samples=confirmed_samples,
                current_round=self.current_round,
                include_baseline=True,
            )
            if retrain_event:
                self.db.record_model_snapshot(
                    exp_id=self.exp_id,
                    version=retrain_event["version"],
                    round_num=self.current_round,
                    samples=retrain_event["training_samples"],
                    metrics=retrain_event["validation_metrics"],
                )

        # 10. Regression pass check (every 10 rounds)
        regression_report = None
        if self.current_round % 10 == 0:
            regression_report = self.regression.run_regression_pass(
                exp_id=self.exp_id,
                current_detector=self.detector,
                current_archive=self.archive,
                current_round=self.current_round,
            )

        # 11. Persist round record to SQLite
        round_record = {
            "experiment_id": self.exp_id,
            "round_number": self.current_round,
            "category": category,
            "injection_point": injection_point,
            "strategy": strategy,
            "transformations": applied_transforms,
            "payload": payload,
            "status_code": exec_result.status_code,
            "duration_ms": round(exec_result.duration_ms, 2),
            "target_compromised": target_compromised,
            "detector_outcome": verdict.verdict_label,
            "rule_fired": verdict.rule_fired,
            "ml_confidence": verdict.ml_confidence,
            "one_line_reason": verdict.one_line_summary,
            "novelty_reward": novelty_reward,
            "fitness_score": round(total_fitness, 3),
        }
        self.db.insert_round(round_record)
        self.db.update_experiment_status(self.exp_id, "running", self.current_round)

        # 12. Assemble event packet for SSE broadcast
        event_payload = {
            **round_record,
            "evidence_snippet": exec_result.evidence_snippet,
            "detector_version": self.detector.version_tag,
            "archive_occupied": self.archive.total_occupied,
            "archive_coverage": round(self.archive.coverage_ratio * 100, 1),
            "bandit_stats": self.bandit.get_stats(),
            "retrain_event": retrain_event,
            "regression_report": {
                "detection_rate": regression_report.detection_rate,
                "summary": regression_report.summary,
            } if regression_report else None,
        }

        self._broadcast_event(event_payload)
        return event_payload
