from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StartExperimentRequest(BaseModel):
    name: str = "CyberRanger Live Experiment"
    total_rounds: int = Field(default=20, ge=1, le=100)
    seed: Optional[int] = 42
    cadence_rounds: int = Field(default=5, ge=1, le=20)
    enable_llm: bool = False


class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(Confirmed|Rejected|Duplicate)$")
    note: Optional[str] = ""


class ExperimentSummary(BaseModel):
    id: str
    name: str
    status: str
    total_rounds: int
    current_round: int
    seed: Optional[int]
    created_at: float
    updated_at: float


class StatsResponse(BaseModel):
    current_round: int
    total_rounds: int
    status: str
    detector_version: str
    detection_rate: float
    evasion_rate: float
    total_compromises: int
    total_blocked: int
    total_clean: int
    active_rules_count: int
    archive_occupied: int
    archive_capacity: int
    archive_coverage: float
    bandit_stats: Dict[str, Any]
    pending_reviews_count: int
