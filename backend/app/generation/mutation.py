import random
from typing import Tuple, Optional
from app.generation.ast import GrammarNode
from app.generation.grammars import GrammarEngine


class GrammarMutator:
    """Performs BNF-guided syntactic mutations on test case derivation trees."""

    def __init__(self, engine: GrammarEngine, seed: Optional[int] = None) -> None:
        self.engine = engine
        self.rng = random.Random(seed)

    def set_seed(self, seed: int) -> None:
        self.rng.seed(seed)
        self.engine.set_seed(seed)

    def mutate(self, tree: GrammarNode, category: str) -> Tuple[GrammarNode, str]:
        """Selects a non-terminal derivation node and re-expands it via BNF production rules.
        
        Returns the mutated AST clone and a human-readable mutation description.
        """
        cloned_tree = tree.clone()
        non_terminals = cloned_tree.get_all_nonterminals()

        # Filter out nodes that don't have multiple alternative productions
        category_grammar = self.engine.definitions.get(category, {})
        eligible_nodes = [
            n for n in non_terminals
            if n.rule_name in category_grammar and len(category_grammar[n.rule_name]) > 0
        ]

        if not eligible_nodes:
            # Fallback: re-expand the whole tree
            fresh = self.engine.expand(category)
            return fresh, f"Complete tree regenerated for {category}"

        # Choose a target node to mutate
        target_node = self.rng.choice(eligible_nodes)
        old_val = target_node.to_string()

        # Re-expand the selected production rule
        fresh_subtree = self.engine.re_expand_rule(category, target_node.rule_name)

        # Replace children of target node
        target_node.children = fresh_subtree.children
        new_val = target_node.to_string()

        description = f"Mutated {target_node.rule_name}: '{old_val}' -> '{new_val}'"
        return cloned_tree, description
