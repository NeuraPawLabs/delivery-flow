from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ControllerState(StrEnum):
    DISCUSSING_REQUIREMENT = "discussing_requirement"
    WRITING_SPEC = "writing_spec"
    PLANNING = "planning"
    RUNNING_DEV = "running_dev"
    RUNNING_REVIEW = "running_review"
    RUNNING_FIX = "running_fix"
    RUNNING_FINALIZE = "running_finalize"
    WAITING_FOR_OWNER = "waiting_for_owner"
    COMPLETED = "completed"


class NormalizedReviewResult(StrEnum):
    PASS = "pass"
    BLOCKER = "blocker"
    NEEDS_OWNER_DECISION = "needs_owner_decision"


class StopReason(StrEnum):
    PASS = "pass"
    NEEDS_OWNER_DECISION = "needs_owner_decision"
    SAME_BLOCKER = "same_blocker_after_two_fix_review_cycles"
    VERIFICATION_UNAVAILABLE = "required_verification_cannot_be_completed_with_available_evidence"


@dataclass(frozen=True)
class BlockerIdentity:
    contract_area: str
    failure_kind: str
    expected_resolution: str
