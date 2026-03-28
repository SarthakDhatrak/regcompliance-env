from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class Observation(BaseModel):
    task_id: str
    documents: Dict[str, str]
    task_goal: str
    rules_to_check: List[str]
    step_number: int


class IssueFlag(BaseModel):
    issue_id: str
    severity: Literal["low", "medium", "high"]
    clause_ref: str
    reason: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class Action(BaseModel):
    issues: List[IssueFlag]


class Reward(BaseModel):
    score: float
    issues_found: int
    issues_missed: int
    false_positives: int
    confidence_bonus: float
    done: bool
    feedback: str
