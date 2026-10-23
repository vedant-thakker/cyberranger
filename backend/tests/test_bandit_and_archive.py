import pytest
from app.generation.archive import MapElitesArchive, EliteCandidate
from app.generation.bandit import UCB1Bandit


def test_map_elites_novelty_and_replacement():
    archive = MapElitesArchive()
    assert archive.total_occupied == 0
    
    # 1. First candidate in an empty cell -> novelty reward 1.0
    is_new, reward, msg = archive.insert(
        category="sqli",
        injection_point="id_param",
        evasion_technique="none",
        detector_outcome="evaded",
        payload="1' OR '1'='1",
        tree=None,
        fitness_score=0.8,
        round_num=1,
    )
    assert is_new is True
    assert reward == 1.0
    assert archive.total_occupied == 1
    
    # 2. Candidate with higher fitness in the same cell -> replacement reward 0.2
    is_new, reward, msg = archive.insert(
        category="sqli",
        injection_point="id_param",
        evasion_technique="none",
        detector_outcome="evaded",
        payload="admin' OR 1=1 --",
        tree=None,
        fitness_score=0.95,
        round_num=2,
    )
    assert is_new is False
    assert reward == 0.2
    assert archive.total_occupied == 1  # Still 1 cell occupied
    
    # Verify the cell was updated to the higher fitness candidate
    key = ("sqli", "id_param", "none", "evaded")
    assert archive.grid[key].payload == "admin' OR 1=1 --"
    assert archive.grid[key].fitness_score == 0.95
    
    # 3. Candidate with lower fitness in the same cell -> no replacement (reward 0.0)
    is_new, reward, msg = archive.insert(
        category="sqli",
        injection_point="id_param",
        evasion_technique="none",
        detector_outcome="evaded",
        payload="inferior",
        tree=None,
        fitness_score=0.5,
        round_num=3,
    )
    assert is_new is False
    assert reward == 0.0
    assert archive.grid[key].payload == "admin' OR 1=1 --"


def test_map_elites_summary_and_coverage():
    archive = MapElitesArchive()
    archive.insert("xss", "name_param", "url_encode", "blocked", "<script>alert(1)</script>", None, 0.7, 1)
    archive.insert("cmdi", "ip_param", "comment_placement", "evaded", "echo CR_TEST_PING", None, 0.9, 2)
    
    assert archive.total_occupied == 2
    assert archive.coverage_ratio > 0.0
    
    summary = archive.get_summary_list()
    assert len(summary) == 2
    assert summary[0]["category"] == "xss"


def test_ucb1_bandit_exploration_and_exploitation():
    bandit = UCB1Bandit(seed=42)
    
    # When no crossover candidates exist, genetic_crossover should not be chosen
    first_arms = set()
    for _ in range(3):
        arm = bandit.select_arm(has_crossover_candidates=False)
        assert arm != "genetic_crossover"
        first_arms.add(arm)
        bandit.update(arm, reward=0.5)
    
    assert len(first_arms) == 3  # Explored all 3 eligible arms
    
    # Over a multi-round game where grammar_mutation consistently yields 2.0 and others yield 0.1,
    # the bandit should pull grammar_mutation significantly more than other arms.
    for _ in range(50):
        arm = bandit.select_arm(has_crossover_candidates=False)
        r = 2.0 if arm == "grammar_mutation" else 0.1
        bandit.update(arm, reward=r)
    
    stats = bandit.get_stats()
    assert stats["grammar_mutation"]["pull_count"] > stats["combinatorial_transform"]["pull_count"]
    assert stats["grammar_mutation"]["pull_count"] > stats["structural_proposal"]["pull_count"]
    assert stats["grammar_mutation"]["mean_reward"] > 1.5
