from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ValidationError
from app.generation.ast import GrammarNode
from app.generation.grammars import GrammarEngine


class StructuralProposal(BaseModel):
    """Schema for structural-only proposals. Strictly validates structure; contains NO payload strings."""
    category: Literal["sqli", "xss", "cmdi", "path_traversal"]
    pattern_type: Literal[
        "tautology_with_comment",
        "union_probe",
        "event_reflection",
        "script_injection",
        "command_chain",
        "command_pipe",
        "deep_relative_traversal",
        "null_terminated_traversal",
    ]
    comment_style: Literal["inline_block", "hash", "dash_dash", "none"] = "none"
    whitespace_mode: Literal["space", "comment", "plus", "url_hex"] = "space"
    casing_mode: Literal["standard", "upper", "lower", "alternating"] = "standard"


class LLMStructureProposer:
    """Interface for structural proposals.
    
    Default: DISABLED.
    Never accepts or outputs arbitrary executable payload strings.
    Always falls back safely to grammar generation.
    """

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    def propose(self, category: str) -> Optional[StructuralProposal]:
        """Returns a validated structural proposal, or None if disabled/failed."""
        if not self.enabled:
            return None

        # When enabled without an external LLM key, generate an algorithmic structural template
        try:
            pattern_map = {
                "sqli": "tautology_with_comment",
                "xss": "event_reflection",
                "cmdi": "command_chain",
                "path_traversal": "deep_relative_traversal",
            }
            return StructuralProposal(
                category=category,  # type: ignore
                pattern_type=pattern_map.get(category, "tautology_with_comment"),  # type: ignore
                comment_style="inline_block",
                whitespace_mode="space",
                casing_mode="standard",
            )
        except ValidationError:
            return None

    def render_to_grammar_tree(
        self, proposal: StructuralProposal, engine: GrammarEngine
    ) -> GrammarNode:
        """Renders a validated structural proposal into a concrete AST using grammar rules."""
        # Always safe: delegates rendering strictly to the BNF grammar
        return engine.expand(proposal.category)
