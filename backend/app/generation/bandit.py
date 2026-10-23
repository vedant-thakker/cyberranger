import math
import random
from typing import Dict, List, Optional, Any


class UCB1Bandit:
    """Upper Confidence Bound (UCB1) multi-armed bandit for adaptive strategy selection.
    
    Balances exploration of less-tested generation strategies with exploitation
    of strategies yielding high measured novelty and fitness rewards.
    """

    OPERATORS = [
        "grammar_mutation",
        "genetic_crossover",
        "combinatorial_transform",
        "structural_proposal",
    ]

    def __init__(self, c_exploration: float = 1.414, seed: Optional[int] = None) -> None:
        self.c = c_exploration
        self.rng = random.Random(seed)
        self.total_rounds = 0
        self.counts: Dict[str, int] = {op: 0 for op in self.OPERATORS}
        self.rewards: Dict[str, float] = {op: 0.0 for op in self.OPERATORS}
        self.history: List[Dict[str, Any]] = []

    def set_seed(self, seed: int) -> None:
        self.rng.seed(seed)

    def select_arm(self, has_crossover_candidates: bool = False) -> str:
        """Selects the operator arm with the highest UCB1 score.
        
        If an arm has never been tried (N_i == 0), it is selected first for initial exploration.
        If crossover candidates are unavailable, genetic_crossover is skipped.
        """
        eligible_arms = list(self.OPERATORS)
        if not has_crossover_candidates:
            # Cannot do crossover if archive has fewer than 2 candidates
            eligible_arms = [op for op in eligible_arms if op != "genetic_crossover"]

        # Initial exploration: try every untried eligible arm once
        untried = [op for op in eligible_arms if self.counts[op] == 0]
        if untried:
            return self.rng.choice(untried)

        # Calculate UCB1 score for each eligible arm
        best_arm = eligible_arms[0]
        best_score = -float("inf")

        for arm in eligible_arms:
            n_i = self.counts[arm]
            mean_reward = self.rewards[arm] / n_i
            # UCB1 = mean + c * sqrt( (2 * ln(N)) / N_i )
            bonus = self.c * math.sqrt((2.0 * math.log(max(1, self.total_rounds))) / n_i)
            ucb_score = mean_reward + bonus

            if ucb_score > best_score:
                best_score = ucb_score
                best_arm = arm

        return best_arm

    def update(self, arm: str, reward: float) -> None:
        """Updates selection counts and observed rewards for the chosen arm."""
        if arm not in self.counts:
            self.counts[arm] = 0
            self.rewards[arm] = 0.0

        self.total_rounds += 1
        self.counts[arm] += 1
        self.rewards[arm] += reward

        self.history.append({
            "round": self.total_rounds,
            "selected_arm": arm,
            "reward": round(reward, 3),
            "counts": dict(self.counts),
            "mean_rewards": {
                op: round(self.rewards[op] / max(1, self.counts[op]), 3)
                for op in self.OPERATORS
            },
        })

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Returns statistical overview of each operator arm for the dashboard."""
        stats = {}
        for op in self.OPERATORS:
            count = self.counts[op]
            mean_r = self.rewards[op] / count if count > 0 else 0.0
            stats[op] = {
                "pull_count": count,
                "total_reward": round(self.rewards[op], 3),
                "mean_reward": round(mean_r, 3),
                "selection_percentage": round((count / max(1, self.total_rounds)) * 100, 1),
            }
        return stats
