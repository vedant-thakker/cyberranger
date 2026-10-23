import random
from typing import Tuple, Optional
from app.generation.ast import GrammarNode


class GeneticCrossover:
    """Combines structural features from two parent test cases at compatible grammar boundaries."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = random.Random(seed)

    def set_seed(self, seed: int) -> None:
        self.rng.seed(seed)

    def crossover(
        self, parent1: GrammarNode, parent2: GrammarNode, category: str
    ) -> Tuple[Optional[GrammarNode], str]:
        """Exchanges compatible subtrees between parent1 and parent2.
        
        Returns the offspring AST and a lineage/crossover summary.
        """
        p1_nodes = parent1.get_all_nonterminals()
        p2_nodes = parent2.get_all_nonterminals()

        # Group subtrees by rule name
        p1_rules = {node.rule_name for node in p1_nodes if node.rule_name != "<start>"}
        p2_rules = {node.rule_name for node in p2_nodes if node.rule_name != "<start>"}

        compatible_rules = list(p1_rules.intersection(p2_rules))

        if not compatible_rules:
            # If no identical non-root rule is shared, clone parent1 with notice
            return parent1.clone(), "No compatible crossover boundary found; preserved parent1"

        chosen_rule = self.rng.choice(compatible_rules)

        # Select candidate nodes
        p1_candidates = [n for n in p1_nodes if n.rule_name == chosen_rule]
        p2_candidates = [n for n in p2_nodes if n.rule_name == chosen_rule]

        if not p1_candidates or not p2_candidates:
            return parent1.clone(), "Crossover candidate selection failed"

        target_in_p1 = self.rng.choice(p1_candidates)
        source_in_p2 = self.rng.choice(p2_candidates)

        # Build offspring from parent1 clone
        offspring = parent1.clone()
        matching_targets = offspring.find_nodes_by_rule(chosen_rule)

        if matching_targets:
            replacement_target = self.rng.choice(matching_targets)
            old_str = replacement_target.to_string()
            replacement_target.children = [c.clone() if isinstance(c, GrammarNode) else c for c in source_in_p2.children]
            new_str = replacement_target.to_string()
            description = (
                f"Spliced rule {chosen_rule}: replaced '{old_str}' with '{new_str}' from parent 2"
            )
            return offspring, description

        return parent1.clone(), "Offspring boundary match failed"
