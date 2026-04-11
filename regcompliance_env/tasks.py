from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

# Root of the project: env/ is one level below project root, data/ is a sibling.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"

SUPPORTED_TASKS = {"task1", "task2", "task3"}

# Human-readable goal descriptions and rules per task.
_TASK_METADATA: Dict[str, Dict[str, object]] = {
    "task1": {
        "task_goal": (
            "Review the privacy policy document for NovaTech Solutions Pvt Ltd "
            "and identify any missing or non-compliant clauses under Indian data "
            "protection law."
        ),
        "rules_to_check": [
            "DPDP Act 2023 Section 8(7) - Data retention period must be specified",
            "IT Act 2000 Section 43A - Reasonable security practices",
            "IT (Intermediary Guidelines) Rules 2021 - Grievance Officer designation",
        ],
    },
    "task2": {
        "task_goal": (
            "Compare the vendor service agreement with CloudServe Ltd against "
            "NovaTech's standard terms of service and identify any cross-document "
            "conflicts, especially around jurisdiction and governing law."
        ),
        "rules_to_check": [
            "Civil Procedure Code 1908 - Jurisdiction consistency across contracts",
            "Indian Contract Act 1872 Section 28 - Restraint of legal proceedings",
            "Arbitration and Conciliation Act 1996 - Dispute resolution mechanisms",
        ],
    },
    "task3": {
        "task_goal": (
            "Conduct a full due diligence audit of NovaTech Solutions Pvt Ltd by "
            "reviewing all five corporate and operational documents. Identify all "
            "compliance violations, missing clauses, cross-document conflicts, and "
            "regulatory gaps under applicable Indian law."
        ),
        "rules_to_check": [
            "DPDP Act 2023 - Data retention, grievance officer, data processor agreements",
            "FEMA 2000 / NDI Rules 2019 - Foreign director and foreign investment compliance",
            "Arbitration and Conciliation Act 1996 - Arbitration clauses in vendor contracts",
            "Companies Act 2013 / SEBI ESOP Regulations - Equity vesting schedules",
            "Copyright Act 1957 Sections 17-18 - IP assignment from employees",
            "Civil Procedure Code 1908 - Jurisdiction consistency across documents",
            "Indian Contract Act 1872 Section 27 - Enforceability of non-compete clauses",
        ],
    },
}


class TaskLoader:
    """Loads task documents and ground truth from the data/ directory."""

    def load_task(self, task_id: str) -> Tuple[Dict[str, str], dict]:
        """Load documents and ground truth for the given task_id.

        Args:
            task_id: One of 'task1', 'task2', 'task3'.

        Returns:
            A tuple of:
              - documents: dict mapping filename (str) to file content (str)
              - ground_truth: parsed ground truth dict

        Raises:
            ValueError: If task_id is not supported.
            FileNotFoundError: If the task directory or ground truth file is missing.
        """
        if task_id not in SUPPORTED_TASKS:
            raise ValueError(
                f"Unknown task_id '{task_id}'. "
                f"Supported tasks: {sorted(SUPPORTED_TASKS)}"
            )

        task_dir = _DATA_DIR / task_id
        if not task_dir.is_dir():
            raise FileNotFoundError(
                f"Task directory not found: {task_dir}"
            )

        # Load ground truth
        ground_truth_path = task_dir / "ground_truth.json"
        if not ground_truth_path.is_file():
            raise FileNotFoundError(
                f"Ground truth file not found: {ground_truth_path}"
            )
        with ground_truth_path.open(encoding="utf-8") as f:
            ground_truth = json.load(f)

        # Load all non-ground-truth files as documents
        documents: Dict[str, str] = {}
        for file_path in sorted(task_dir.iterdir()):
            if file_path.name == "ground_truth.json":
                continue
            if file_path.is_file():
                documents[file_path.name] = file_path.read_text(encoding="utf-8")

        return documents, ground_truth

    def get_task_metadata(self, task_id: str) -> Dict[str, object]:
        """Return task_goal and rules_to_check for a given task."""
        if task_id not in SUPPORTED_TASKS:
            raise ValueError(
                f"Unknown task_id '{task_id}'. "
                f"Supported tasks: {sorted(SUPPORTED_TASKS)}"
            )
        return _TASK_METADATA[task_id]
