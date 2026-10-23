from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional
from app.generation.ast import GrammarNode


@dataclass
class EliteCandidate:
    """An elite test structure occupying a MAP-Elites behavioral niche."""
    category: str
    injection_point: str
    evasion_technique: str
    detector_outcome: str
    payload: str
    tree: Optional[GrammarNode]
    fitness_score: float
    round_discovered: int
    timestamp: float


class MapElitesArchive:
    """MAP-Elites multidimensional archive indexing test candidates by behavioral descriptors.
    
    Dimensions:
    - category: (sqli, xss, cmdi, path_traversal)
    - injection_point: (id_param, name_param, ip_param, page_param)
    - evasion_technique: (none, case_variation, whitespace_sub, url_encode, hex_encode, unicode_encode, comment_placement, composite)
    - detector_outcome: (clean, blocked, evaded, unknown)
    """

    CATEGORIES = ["sqli", "xss", "cmdi", "path_traversal"]
    INJECTION_POINTS = ["id_param", "name_param", "ip_param", "page_param"]
    EVASION_TECHNIQUES = [
        "none",
        "case_variation",
        "whitespace_sub",
        "url_encode",
        "hex_encode",
        "unicode_encode",
        "comment_placement",
        "composite",
    ]
    DETECTOR_OUTCOMES = ["clean", "blocked", "evaded", "unknown"]

    def __init__(self) -> None:
        self.grid: Dict[Tuple[str, str, str, str], EliteCandidate] = {}
        self.novelty_history: List[Dict] = []
        self._total_capacity = (
            len(self.CATEGORIES)
            * len(self.INJECTION_POINTS)
            * len(self.EVASION_TECHNIQUES)
            * len(self.DETECTOR_OUTCOMES)
        )

    @property
    def total_capacity(self) -> int:
        return self._total_capacity

    @property
    def total_occupied(self) -> int:
        return len(self.grid)

    @property
    def coverage_ratio(self) -> float:
        return self.total_occupied / self._total_capacity if self._total_capacity > 0 else 0.0

    def insert(
        self,
        category: str,
        injection_point: str,
        evasion_technique: str,
        detector_outcome: str,
        payload: str,
        tree: Optional[GrammarNode],
        fitness_score: float,
        round_num: int,
    ) -> Tuple[bool, float, str]:
        """Inserts candidate into the MAP-Elites grid.
        
        Returns (is_novel_cell, novelty_reward, message).
        A reward of 1.0 is given for filling a previously empty cell.
        """
        cell_key = (category, injection_point, evasion_technique, detector_outcome)
        now = time.time()

        if cell_key not in self.grid:
            # Discovered a brand new behavioral cell
            candidate = EliteCandidate(
                category=category,
                injection_point=injection_point,
                evasion_technique=evasion_technique,
                detector_outcome=detector_outcome,
                payload=payload,
                tree=tree,
                fitness_score=fitness_score,
                round_discovered=round_num,
                timestamp=now,
            )
            self.grid[cell_key] = candidate
            self.novelty_history.append({
                "round": round_num,
                "cell": cell_key,
                "novelty_reward": 1.0,
                "total_occupied": len(self.grid),
            })
            return True, 1.0, f"Discovered new behavioral cell: {cell_key}"

        # Cell is already occupied; compare fitness
        existing = self.grid[cell_key]
        if fitness_score > existing.fitness_score:
            self.grid[cell_key] = EliteCandidate(
                category=category,
                injection_point=injection_point,
                evasion_technique=evasion_technique,
                detector_outcome=detector_outcome,
                payload=payload,
                tree=tree,
                fitness_score=fitness_score,
                round_discovered=round_num,
                timestamp=now,
            )
            return False, 0.2, f"Replaced existing cell with higher fitness ({fitness_score:.2f} > {existing.fitness_score:.2f})"

        return False, 0.0, "Cell occupied with superior or equal candidate"

    def get_elites_by_category(self, category: str) -> List[EliteCandidate]:
        """Returns all elite candidates belonging to a specific vulnerability category."""
        return [c for c in self.grid.values() if c.category == category]

    def get_summary_list(self) -> List[Dict]:
        """Serializes current archive state for dashboard consumption."""
        summary = []
        for key, candidate in self.grid.items():
            cat, inj, evas, out = key
            summary.append({
                "category": cat,
                "injection_point": inj,
                "evasion_technique": evas,
                "detector_outcome": out,
                "fitness_score": round(candidate.fitness_score, 3),
                "round_discovered": candidate.round_discovered,
                "payload_sample": candidate.payload[:40],
            })
        return summary
