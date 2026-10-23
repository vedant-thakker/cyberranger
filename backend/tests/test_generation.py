import pytest
from app.generation.ast import GrammarNode
from app.generation.grammars import GrammarEngine, GRAMMAR_DEFINITIONS
from app.generation.mutation import GrammarMutator
from app.generation.crossover import GeneticCrossover
from app.generation.transforms import (
    TransformPipeline,
    CaseVariationTransform,
    WhitespaceSubstitutionTransform,
    CommentPlacementTransform,
    URLEncodeTransform,
    HexEncodeTransform,
    UnicodeEncodeTransform,
)
from app.generation.optional_llm import StructuralProposal, LLMStructureProposer
import random


def test_grammar_engine_expansion_all_categories():
    engine = GrammarEngine(seed=42)
    categories = ["sqli", "xss", "cmdi", "path_traversal"]
    
    for cat in categories:
        tree = engine.expand(cat)
        assert isinstance(tree, GrammarNode)
        rendered = tree.to_string()
        assert len(rendered) > 0
        # Check that no BNF rule markers like <start> or <prefix> remain in the string
        assert "<start>" not in rendered
        assert "<prefix>" not in rendered
        assert "<tautology>" not in rendered
        assert "<command>" not in rendered


def test_grammar_mutator():
    engine = GrammarEngine(seed=42)
    mutator = GrammarMutator(engine, seed=42)
    
    # Generate initial tree
    initial_tree = engine.expand("sqli")
    initial_text = initial_tree.to_string()
    
    # Mutate tree
    mutated_tree, desc = mutator.mutate(initial_tree, "sqli")
    mutated_text = mutated_tree.to_string()
    
    assert isinstance(mutated_tree, GrammarNode)
    assert len(desc) > 0
    assert len(mutated_text) > 0


def test_genetic_crossover():
    engine = GrammarEngine(seed=123)
    crossover = GeneticCrossover(seed=123)
    
    # Create two parents from the same category
    parent1 = engine.expand("sqli")
    parent2 = engine.expand("sqli")
    
    offspring, summary = crossover.crossover(parent1, parent2, "sqli")
    assert isinstance(offspring, GrammarNode)
    assert len(summary) > 0
    assert len(offspring.to_string()) > 0


def test_transforms_individual_and_pipeline():
    pipeline = TransformPipeline(seed=42)
    sample_sql = "1' OR '1'='1' UNION SELECT 1, 2"
    
    # Case variation
    cv = CaseVariationTransform()
    varied = cv.apply(sample_sql, random.Random(42))
    assert varied.lower() == sample_sql.lower()
    
    # Whitespace sub
    ws = WhitespaceSubstitutionTransform(style="/**/")
    subbed = ws.apply("SELECT * FROM users", random.Random(42))
    assert "/**/" in subbed
    
    # URL encode
    ue = URLEncodeTransform()
    encoded = ue.apply("<script>alert(1)</script>", random.Random(42))
    assert "%3C" in encoded or "%3c" in encoded or "<" not in encoded
    
    # Hex encode
    he = HexEncodeTransform()
    hexed = he.apply("admin' OR '1'='1", random.Random(42))
    assert "%" in hexed
    
    # Pipeline combination
    combined, names = pipeline.apply_random_combination(sample_sql, max_transforms=2)
    assert len(names) >= 1
    assert len(combined) > 0


def test_optional_llm_proposer_schema():
    proposer = LLMStructureProposer(enabled=False)
    # Disabled by default
    assert proposer.propose("sqli") is None
    
    # Enabled proposer emits valid schema
    proposer.enabled = True
    proposal = proposer.propose("sqli")
    assert proposal is not None
    assert proposal.category == "sqli"
    assert proposal.pattern_type == "tautology_with_comment"
    
    # Render via grammar engine safely
    engine = GrammarEngine(seed=42)
    tree = proposer.render_to_grammar_tree(proposal, engine)
    assert isinstance(tree, GrammarNode)
    assert len(tree.to_string()) > 0
