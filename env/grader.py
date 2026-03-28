from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from env.models import Action, Reward

# Penalty subtracted from score for each false positive.
_FP_PENALTY: float = 0.05

# Extra confidence penalty when agent is overconfident on a false positive.
_CONFIDENCE_FP_EXTRA_PENALTY: float = 0.03

# Bonus added per correctly identified issue when agent confidence >= threshold.
_CONFIDENCE_BONUS_PER_ISSUE: float = 0.02

# Confidence threshold for bonus/penalty rules.
_CONFIDENCE_THRESHOLD: float = 0.8

# Completion bonus when all issues are found with zero false positives.
_COMPLETION_BONUS: float = 0.1

# Credit multiplier for fuzzy (keyword / semantic) matches.
_FUZZY_CREDIT_MULTIPLIER: float = 0.7

# ---------------------------------------------------------------------------
# Semantic keyword groups
# Each entry maps a frozenset of trigger keywords to a list of canonical IDs
# that keywords resolve to.
# ---------------------------------------------------------------------------

_SEMANTIC_MAP: List[Tuple[frozenset, List[str]]] = [
    (
        frozenset({"retention", "data_retention"}),
        ["missing_data_retention_clause"],
    ),
    (
        frozenset({"fema", "foreign_director", "rbi"}),
        ["fema_foreign_director_violation"],
    ),
    (
        frozenset({"arbitration", "dispute"}),
        ["missing_arbitration_clause"],
    ),
    (
        frozenset({"vesting", "equity"}),
        ["missing_equity_vesting_schedule"],
    ),
    (
        frozenset({"ip", "intellectual", "assignment"}),
        ["missing_ip_assignment_clause"],
    ),
    (
        frozenset({"jurisdiction", "conflict", "governing"}),
        ["jurisdiction_conflict_vendor", "jurisdiction_conflict_terms", "jurisdiction_conflict"],
    ),
    (
        frozenset({"noncompete", "non_compete", "restraint"}),
        ["noncompete_exceeds_limit"],
    ),
    (
        frozenset({"grievance", "officer"}),
        ["missing_grievance_officer"],
    ),
    (
        frozenset({"quorum", "board_meeting"}),
        ["missing_board_quorum_definition"],
    ),
    (
        frozenset({"notice_period", "notice"}),
        ["notice_period_exceeds_limit"],
    ),
    (
        frozenset({"board_resolution", "foreign_investment"}),
        ["missing_board_resolution_foreign_investment"],
    ),
    (
        frozenset({"data_processor", "dpa", "processor_agreement"}),
        ["missing_data_processor_agreement_reference"],
    ),
]


@dataclass
class _GradeResult:
    """Intermediate accumulator used during grading."""

    hits_full: int = 0          # correct issues with correct severity (exact match)
    hits_partial: int = 0       # correct issues with wrong severity (exact match)
    hits_fuzzy: int = 0         # correct issues matched via keyword/semantic
    false_positives: int = 0
    confidence_bonus: float = 0.0
    hit_issue_ids: Set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Match helpers
# ---------------------------------------------------------------------------

def _keyword_match(agent_id: str, gt_id: str) -> bool:
    """Return True if all underscore-words from gt_id appear in agent_id."""
    agent_norm = agent_id.lower()
    words = gt_id.lower().split("_")
    return all(w in agent_norm for w in words if w)


def _semantic_match(agent_id: str, gt_id: str) -> bool:
    """Return True if agent_id contains a keyword that maps to gt_id."""
    agent_norm = agent_id.lower()
    for keywords, target_ids in _SEMANTIC_MAP:
        if gt_id not in target_ids:
            continue
        # Check if any keyword from this group appears in agent_id
        for kw in keywords:
            if kw.lower() in agent_norm:
                return True
    return False


def _find_gt_match(
    agent_id: str,
    gt_by_id: Dict[str, dict],
    already_hit: Set[str],
) -> Tuple[Optional[str], str]:
    """Find the best matching ground truth issue for agent_id.

    Returns:
        (matched_gt_id, match_type) where match_type is one of:
        "exact", "keyword", "semantic", or "none".
    """
    agent_id_norm = agent_id.lower()

    # 1. Exact match
    for gt_id in gt_by_id:
        if gt_id in already_hit:
            continue
        if agent_id_norm == gt_id.lower():
            return gt_id, "exact"

    # 2. Keyword match — iterate gt issues in order
    for gt_id in gt_by_id:
        if gt_id in already_hit:
            continue
        if _keyword_match(agent_id_norm, gt_id):
            return gt_id, "keyword"

    # 3. Semantic match
    for gt_id in gt_by_id:
        if gt_id in already_hit:
            continue
        if _semantic_match(agent_id_norm, gt_id):
            return gt_id, "semantic"

    return None, "none"


class Grader:
    """Grades an agent's Action against the ground truth for a task."""

    def grade(self, action: Action, ground_truth: dict) -> Reward:
        """Score the agent's submitted issues against the ground truth.

        Scoring Rules
        -------------
        - Exact match + correct severity  → 1.0 / total_issues  (full credit)
        - Exact match + wrong severity    → 0.5 / total_issues  (partial credit)
        - Keyword/semantic match          → 0.7 / total_issues  (fuzzy credit)
        - False positive (-0.05)         : issue_id does not match any ground truth.
        - Confidence bonus (+0.02)       : correct issue with confidence >= 0.8.
        - Confidence penalty (-0.03)     : false positive with confidence >= 0.8.
        - Completion bonus (+0.1)        : all issues found, zero false positives.
        - Final score clamped to [0.0, 1.0].

        Args:
            action:       The agent's Action containing a list of IssueFlag objects.
            ground_truth: Parsed ground_truth.json dict with 'issues' and 'total_issues'.

        Returns:
            A fully populated Reward object.
        """
        gt_issues: List[dict] = ground_truth.get("issues", [])
        total_issues: int = ground_truth.get("total_issues", len(gt_issues))

        # Build a lookup for matching.
        gt_by_id: Dict[str, dict] = {iss["issue_id"]: iss for iss in gt_issues}

        result = _GradeResult()
        base_score: float = 0.0

        for flag in action.issues:
            matched_gt_id, match_type = _find_gt_match(
                flag.issue_id, gt_by_id, result.hit_issue_ids
            )

            if match_type == "exact":
                gt_issue = gt_by_id[matched_gt_id]
                result.hit_issue_ids.add(matched_gt_id)

                if flag.severity == gt_issue["severity"]:
                    credit = 1.0 / total_issues if total_issues > 0 else 0.0
                    result.hits_full += 1
                else:
                    credit = 0.5 / total_issues if total_issues > 0 else 0.0
                    result.hits_partial += 1

                base_score += credit

                if flag.confidence >= _CONFIDENCE_THRESHOLD:
                    result.confidence_bonus += _CONFIDENCE_BONUS_PER_ISSUE

            elif match_type in ("keyword", "semantic"):
                result.hit_issue_ids.add(matched_gt_id)
                result.hits_fuzzy += 1

                credit = (_FUZZY_CREDIT_MULTIPLIER / total_issues) if total_issues > 0 else 0.0
                base_score += credit

                if flag.confidence >= _CONFIDENCE_THRESHOLD:
                    result.confidence_bonus += _CONFIDENCE_BONUS_PER_ISSUE

            else:
                # False positive
                result.false_positives += 1
                base_score -= _FP_PENALTY

                if flag.confidence >= _CONFIDENCE_THRESHOLD:
                    base_score -= _CONFIDENCE_FP_EXTRA_PENALTY

        issues_found = len(result.hit_issue_ids)
        issues_missed = total_issues - issues_found

        # Apply confidence bonus to overall score
        final_score = base_score + result.confidence_bonus

        # Completion bonus: all issues found with all FULL credit and zero false positives
        perfect = (
            result.hits_full == total_issues
            and result.hits_partial == 0
            and result.hits_fuzzy == 0
            and result.false_positives == 0
        )
        if perfect:
            final_score += _COMPLETION_BONUS

        # Clamp to [0.0, 1.0]
        final_score = max(0.0, min(1.0, final_score))

        feedback = self._build_feedback(
            result=result,
            issues_found=issues_found,
            issues_missed=issues_missed,
            total_issues=total_issues,
            gt_by_id=gt_by_id,
            perfect=perfect,
        )

        return Reward(
            score=round(final_score, 4),
            issues_found=issues_found,
            issues_missed=issues_missed,
            false_positives=result.false_positives,
            confidence_bonus=round(result.confidence_bonus, 4),
            done=True,
            feedback=feedback,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_feedback(
        self,
        result: _GradeResult,
        issues_found: int,
        issues_missed: int,
        total_issues: int,
        gt_by_id: Dict[str, dict],
        perfect: bool,
    ) -> str:
        parts: List[str] = []

        parts.append(
            f"Found {issues_found}/{total_issues} issues "
            f"({result.hits_full} exact, {result.hits_partial} partial severity match, "
            f"{result.hits_fuzzy} fuzzy match). "
            f"False positives: {result.false_positives}. "
            f"Issues missed: {issues_missed}."
        )

        if result.confidence_bonus > 0:
            parts.append(
                f"Confidence bonus earned: +{result.confidence_bonus:.2f} "
                f"(calibrated confidence >= {_CONFIDENCE_THRESHOLD} on correct issues)."
            )

        if perfect:
            parts.append(
                f"Perfect score! Completion bonus of +{_COMPLETION_BONUS} applied."
            )

        if issues_missed > 0:
            missed_ids = [
                iss_id for iss_id in gt_by_id if iss_id not in result.hit_issue_ids
            ]
            missed_str = ", ".join(f"'{m}'" for m in missed_ids)
            parts.append(f"Missed issues: {missed_str}.")

        if result.false_positives > 0:
            parts.append(
                f"Each false positive cost -{_FP_PENALTY} "
                f"(+{_CONFIDENCE_FP_EXTRA_PENALTY} extra if confidence >= {_CONFIDENCE_THRESHOLD})."
            )

        if result.hits_partial > 0:
            parts.append(
                "Some issues had correct issue_id but wrong severity — "
                "partial credit (0.5x) was awarded."
            )

        if result.hits_fuzzy > 0:
            parts.append(
                f"Some issues were matched via keyword/semantic similarity — "
                f"fuzzy credit ({_FUZZY_CREDIT_MULTIPLIER}x) was awarded."
            )

        return " ".join(parts)
