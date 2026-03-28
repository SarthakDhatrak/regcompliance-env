from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

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


@dataclass
class _GradeResult:
    """Intermediate accumulator used during grading."""

    hits_full: int = 0          # correct issues with correct severity
    hits_partial: int = 0       # correct issues with wrong severity
    false_positives: int = 0
    confidence_bonus: float = 0.0
    hit_issue_ids: Set[str] = field(default_factory=set)


class Grader:
    """Grades an agent's Action against the ground truth for a task."""

    def grade(self, action: Action, ground_truth: dict) -> Reward:
        """Score the agent's submitted issues against the ground truth.

        Scoring Rules
        -------------
        - Full credit  (1.0 / total_issues) : issue_id matches AND severity matches.
        - Partial credit (0.5 / total_issues): issue_id matches BUT severity is wrong.
        - False positive (-0.05)            : issue_id does not match any ground truth.
        - Confidence bonus (+0.02 per hit)  : correct issue with confidence >= 0.8.
        - Confidence penalty (-0.03 extra)  : false positive with confidence >= 0.8.
        - Completion bonus (+0.1)           : all issues found, zero false positives.
        - Final score clamped to [0.0, 1.0].

        Args:
            action:       The agent's Action containing a list of IssueFlag objects.
            ground_truth: Parsed ground_truth.json dict with 'issues' and 'total_issues'.

        Returns:
            A fully populated Reward object.
        """
        gt_issues: List[dict] = ground_truth.get("issues", [])
        total_issues: int = ground_truth.get("total_issues", len(gt_issues))

        # Build a lookup for O(1) matching.
        gt_by_id: Dict[str, dict] = {iss["issue_id"]: iss for iss in gt_issues}

        result = _GradeResult()
        base_score: float = 0.0

        for flag in action.issues:
            if flag.issue_id in gt_by_id:
                gt_issue = gt_by_id[flag.issue_id]
                result.hit_issue_ids.add(flag.issue_id)

                if flag.severity == gt_issue["severity"]:
                    # Full credit
                    credit = 1.0 / total_issues if total_issues > 0 else 0.0
                    result.hits_full += 1
                else:
                    # Partial credit - severity mismatch
                    credit = 0.5 / total_issues if total_issues > 0 else 0.0
                    result.hits_partial += 1

                base_score += credit

                # Confidence bonus for correct issues
                if flag.confidence >= _CONFIDENCE_THRESHOLD:
                    result.confidence_bonus += _CONFIDENCE_BONUS_PER_ISSUE

            else:
                # False positive
                result.false_positives += 1
                base_score -= _FP_PENALTY

                # Extra penalty for overconfident false positives
                if flag.confidence >= _CONFIDENCE_THRESHOLD:
                    base_score -= _CONFIDENCE_FP_EXTRA_PENALTY

        issues_found = len(result.hit_issue_ids)
        issues_missed = total_issues - issues_found

        # Apply confidence bonus to overall score
        final_score = base_score + result.confidence_bonus

        # Completion bonus: all issues found with FULL credit (correct severity) and zero false positives
        perfect = (
            result.hits_full == total_issues
            and result.hits_partial == 0
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
            f"({result.hits_full} exact, {result.hits_partial} partial severity match). "
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

        return " ".join(parts)
