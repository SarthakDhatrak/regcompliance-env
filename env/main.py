from __future__ import annotations

from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from env.document_generator import DocumentGenerator
from env.grader import Grader
from env.models import Action, Observation, Reward
from env.tasks import TaskLoader

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="regcompliance-env",
    description=(
        "OpenEnv-compatible environment for training AI agents on Indian "
        "startup legal compliance classification."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Per-task static configuration
# ---------------------------------------------------------------------------

_TASK_GOALS: Dict[str, str] = {
    "task1": (
        "Read the privacy policy and identify all compliance violations "
        "under Indian startup law."
    ),
    "task2": (
        "Read both documents and identify any conflicts between them, "
        "especially around jurisdiction and governing law."
    ),
    "task3": (
        "Conduct a full compliance audit across all 5 documents. "
        "Identify every violation of Indian startup law present."
    ),
}

_TASK_RULES: Dict[str, List[str]] = {
    "task1": [
        "DPDP Act 2023",
        "IT Act 2000",
    ],
    "task2": [
        "Civil Procedure Code 1908",
        "Indian Contract Act 1872",
    ],
    "task3": [
        "DPDP Act 2023",
        "FEMA 2000",
        "Companies Act 2013",
        "Arbitration Act 1996",
        "Copyright Act 1957",
        "IT Act 2000",
        "Shops and Establishments Act",
    ],
}

# ---------------------------------------------------------------------------
# Module-level state (no database)
# ---------------------------------------------------------------------------

_loader = TaskLoader()
_grader = Grader()

_state: Dict[str, Any] = {
    "task_id": None,
    "documents": {},       # filename -> content
    "ground_truth": None,
    "step_number": 0,
}


def _require_task() -> None:
    """Raise HTTP 400 if no task has been loaded yet."""
    if _state["task_id"] is None:
        raise HTTPException(status_code=400, detail="Call /reset first")


def _current_observation() -> Observation:
    return Observation(
        task_id=_state["task_id"],
        documents=_state["documents"],
        task_goal=_TASK_GOALS[_state["task_id"]],
        rules_to_check=_TASK_RULES[_state["task_id"]],
        step_number=_state["step_number"],
    )


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_id: str
    use_generator: bool = True
    seed: Optional[int] = None


class StepResponse(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any]


class StateResponse(BaseModel):
    task_id: Optional[str]
    step_number: int
    documents_loaded: List[str]
    is_ready: bool


class HealthResponse(BaseModel):
    status: str
    environment: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    """Liveness check."""
    return HealthResponse(status="ok", environment="regcompliance-env")


@app.post("/reset", response_model=Observation, tags=["env"])
def reset(body: ResetRequest) -> Observation:
    """Reset the environment and load a task.

    - **task_id**: one of ``task1``, ``task2``, ``task3``.
    - **use_generator** *(default True)*: when ``True``, generates fresh synthetic
      documents each call so agents cannot memorise the text. When ``False``,
      loads the original static files from ``data/``.
    - **seed** *(optional)*: integer seed for reproducible document generation.

    Returns an ``Observation`` containing task documents, goal, and rules.
    """
    task_id = body.task_id.strip().lower()

    # Always load ground truth from data/ (source of truth for grading)
    try:
        _, ground_truth = _loader.load_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Optionally generate fresh documents
    if body.use_generator:
        gen = DocumentGenerator(seed=body.seed)
        _gen_methods = {
            "task1": gen.generate_task1_docs,
            "task2": gen.generate_task2_docs,
            "task3": gen.generate_task3_docs,
        }
        documents = _gen_methods[task_id]()
    else:
        documents, _ = _loader.load_task(task_id)

    _state["task_id"] = task_id
    _state["documents"] = documents
    _state["ground_truth"] = ground_truth
    _state["step_number"] = 0
    _state["use_generator"] = body.use_generator
    _state["seed"] = body.seed

    return _current_observation()


@app.post("/step", response_model=StepResponse, tags=["env"])
def step(action: Action) -> StepResponse:
    """Submit an Action (list of IssueFlags) and receive a graded Reward.

    You must call /reset before calling /step.
    """
    _require_task()

    reward: Reward = _grader.grade(action, _state["ground_truth"])
    _state["step_number"] += 1

    return StepResponse(
        observation=_current_observation(),
        reward=reward,
        done=True,
        info={
            "task_id": _state["task_id"],
            "step": _state["step_number"],
        },
    )


@app.get("/state", response_model=StateResponse, tags=["env"])
def state() -> StateResponse:
    """Return the current environment state (read-only)."""
    return StateResponse(
        task_id=_state["task_id"],
        step_number=_state["step_number"],
        documents_loaded=list(_state["documents"].keys()),
        is_ready=_state["task_id"] is not None,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("env.main:app", host="0.0.0.0", port=7860, reload=True)
