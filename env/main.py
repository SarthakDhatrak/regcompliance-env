from __future__ import annotations

import datetime
import pathlib
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from env.document_generator import DocumentGenerator
from env.grader import Grader
from env.models import Action, Observation, Reward
from env.tasks import TaskLoader

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

# Path to the ui/ folder (one level above the env/ package)
_UI_DIR: pathlib.Path = pathlib.Path(__file__).resolve().parent.parent / "ui"

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

# Episode replay — cleared on every /reset call.
episode_history: List[Dict[str, Any]] = []

# Leaderboard — persists across episodes; max 10 entries sorted by score desc.
leaderboard: List[Dict[str, Any]] = []
_total_runs: int = 0          # monotonically increasing run counter


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


class RootResponse(BaseModel):
    name: str
    version: str
    description: str
    status: str
    endpoints: List[str]
    tasks: List[Dict[str, str]]
    space_url: str
    docs_url: str
    leaderboard_url: str
    replay_url: str


class ReplayResponse(BaseModel):
    task_id: Optional[str]
    total_steps: int
    final_score: float
    episode: List[Dict[str, Any]]
    summary: str


class LeaderboardResponse(BaseModel):
    total_runs: int
    leaderboard: List[Dict[str, Any]]
    best_score: float
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    """Serve the monitoring dashboard UI."""
    return FileResponse(str(_UI_DIR / "index.html"), media_type="text/html")


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
    global episode_history

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

    # Clear episode history for the new episode
    episode_history = []

    return _current_observation()


@app.post("/step", response_model=StepResponse, tags=["env"])
def step(action: Action, request: Request) -> StepResponse:
    """Submit an Action (list of IssueFlags) and receive a graded Reward.

    You must call /reset before calling /step.
    Optionally pass X-Model-Name header to identify your agent on the leaderboard.
    """
    global _total_runs

    _require_task()

    reward: Reward = _grader.grade(action, _state["ground_truth"])
    _state["step_number"] += 1
    now_iso: str = datetime.datetime.utcnow().isoformat() + "Z"

    # --- Episode history ---
    episode_history.append(
        {
            "step_number": _state["step_number"],
            "action_taken": [
                {
                    "issue_id": f.issue_id,
                    "severity": f.severity,
                    "confidence": f.confidence,
                    "explanation": getattr(f, "explanation", ""),
                }
                for f in action.issues
            ],
            "reward_received": reward.score,
            "issues_found": reward.issues_found,
            "false_positives": reward.false_positives,
            "feedback": reward.feedback,
            "timestamp": now_iso,
        }
    )

    done = True  # single-step episodes

    # --- Leaderboard update when episode is done ---
    if done:
        _total_runs += 1
        model_hint: str = request.headers.get("X-Model-Name", "anonymous")
        new_entry: Dict[str, Any] = {
            "task_id": _state["task_id"],
            "score": reward.score,
            "issues_found": reward.issues_found,
            "false_positives": reward.false_positives,
            "model_hint": model_hint,
            "timestamp": now_iso,
        }
        _update_leaderboard(new_entry)

    return StepResponse(
        observation=_current_observation(),
        reward=reward,
        done=done,
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


@app.get("/replay", response_model=ReplayResponse, tags=["env"])
def replay() -> ReplayResponse:
    """Return a full replay of the current episode."""
    total_steps = len(episode_history)
    final_score: float = episode_history[-1]["reward_received"] if episode_history else 0.0
    issues_found: int = episode_history[-1]["issues_found"] if episode_history else 0
    gt_issues: int = len(_state["ground_truth"].get("issues", [])) if _state["ground_truth"] else 0
    summary = (
        f"Agent found {issues_found}/{gt_issues} issues in {total_steps} step(s) "
        f"with final score {final_score:.4f}"
    )
    return ReplayResponse(
        task_id=_state["task_id"],
        total_steps=total_steps,
        final_score=final_score,
        episode=episode_history,
        summary=summary,
    )


@app.get("/leaderboard", response_model=LeaderboardResponse, tags=["meta"])
def get_leaderboard() -> LeaderboardResponse:
    """Return the in-memory top-10 leaderboard."""
    ranked = [
        {**entry, "rank": idx + 1}
        for idx, entry in enumerate(leaderboard)
    ]
    best_score: float = leaderboard[0]["score"] if leaderboard else 0.0
    return LeaderboardResponse(
        total_runs=_total_runs,
        leaderboard=ranked,
        best_score=best_score,
        message=(
            "Submit your agent score at "
            "https://huggingface.co/spaces/sarthakdhatrak/regcompliance-env"
        ),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _update_leaderboard(entry: Dict[str, Any]) -> None:
    """Insert entry into leaderboard, keeping top-10 sorted by score descending."""
    if len(leaderboard) >= 10 and entry["score"] <= leaderboard[-1]["score"]:
        return  # Not good enough to enter top-10
    leaderboard.append(entry)
    leaderboard.sort(key=lambda e: e["score"], reverse=True)
    del leaderboard[10:]  # trim to max 10


# ---------------------------------------------------------------------------
# Static UI files — mount AFTER all API routes so it doesn't shadow them.
# ---------------------------------------------------------------------------

if _UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(_UI_DIR), html=True), name="ui-static")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("env.main:app", host="0.0.0.0", port=7860, reload=True)
