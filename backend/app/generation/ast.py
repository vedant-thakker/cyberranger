from __future__ import annotations
import random
from typing import List, Union, Optional, Tuple


class GrammarNode:
    """An Abstract Syntax Tree (AST) node representing a derivation in a BNF grammar."""

    def __init__(self, rule_name: str, children: Optional[List[Union[str, GrammarNode]]] = None) -> None:
        self.rule_name = rule_name
        self.children: List[Union[str, GrammarNode]] = children if children is not None else []

    def is_terminal(self) -> bool:
        return len(self.children) == 0 or all(isinstance(c, str) for c in self.children)

    def to_string(self) -> str:
        """Flattens the AST into its rendered textual representation."""
        result = []
        for child in self.children:
            if isinstance(child, str):
                result.append(child)
            elif isinstance(child, GrammarNode):
                result.append(child.to_string())
        return "".join(result)

    def clone(self) -> GrammarNode:
        """Deep copy of the grammar tree."""
        new_children: List[Union[str, GrammarNode]] = []
        for child in self.children:
            if isinstance(child, str):
                new_children.append(child)
            elif isinstance(child, GrammarNode):
                new_children.append(child.clone())
        return GrammarNode(self.rule_name, new_children)

    def get_all_nonterminals(self) -> List[GrammarNode]:
        """Collects all non-terminal nodes in this tree."""
        nodes = [self]
        for child in self.children:
            if isinstance(child, GrammarNode):
                nodes.extend(child.get_all_nonterminals())
        return nodes

    def find_nodes_by_rule(self, rule_name: str) -> List[GrammarNode]:
        """Finds all subtrees rooted with a specific rule name."""
        matches = []
        if self.rule_name == rule_name:
            matches.append(self)
        for child in self.children:
            if isinstance(child, GrammarNode):
                matches.extend(child.find_nodes_by_rule(rule_name))
        return matches

    def replace_child(self, old_node: GrammarNode, new_node: GrammarNode) -> bool:
        """Replaces a child node instance with a new node."""
        for i, child in enumerate(self.children):
            if child is old_node:
                self.children[i] = new_node
                return True
            if isinstance(child, GrammarNode):
                if child.replace_child(old_node, new_node):
                    return True
        return False
