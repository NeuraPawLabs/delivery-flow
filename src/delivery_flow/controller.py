from __future__ import annotations

from enum import StrEnum


class ControllerState(StrEnum):
    DISCUSSING_REQUIREMENT = "discussing_requirement"
    WRITING_SPEC = "writing_spec"
    PLANNING = "planning"
    RUNNING_DEV = "running_dev"
    RUNNING_REVIEW = "running_review"
    RUNNING_FIX = "running_fix"
    WAITING_FOR_OWNER = "waiting_for_owner"
    COMPLETED = "completed"


class NormalizedReviewResult(StrEnum):
    PASS = "pass"
    BLOCKER = "blocker"
    NEEDS_OWNER_DECISION = "needs_owner_decision"


class MainAgentLoopController:
    def __init__(self, capability_detector: object | None = None) -> None:
        self.capability_detector = capability_detector
        self.state = ControllerState.DISCUSSING_REQUIREMENT
        self.mode: str | None = None

    def select_mode(self) -> str:
        if self.capability_detector is None:
            raise RuntimeError("Capability detector is required for explicit mode selection")

        if not hasattr(self.capability_detector, "has_superpowers"):
            raise RuntimeError("Capability detector must expose `has_superpowers`")

        has_superpowers = bool(self.capability_detector.has_superpowers)
        self.mode = "superpowers-backed" if has_superpowers else "fallback"
        return self.mode

    def mode_banner(self) -> str:
        if self.mode is None:
            raise RuntimeError("Mode must be selected before banner emission")

        return f"mode={self.mode}"

    def normalize_review_result(self, raw_result: str) -> NormalizedReviewResult:
        normalized_map = {
            "pass": NormalizedReviewResult.PASS,
            "approved": NormalizedReviewResult.PASS,
            "blocker": NormalizedReviewResult.BLOCKER,
            "changes_requested": NormalizedReviewResult.BLOCKER,
            "needs_owner_decision": NormalizedReviewResult.NEEDS_OWNER_DECISION,
            "owner_input_required": NormalizedReviewResult.NEEDS_OWNER_DECISION,
        }

        try:
            return normalized_map[raw_result]
        except KeyError as exc:
            raise RuntimeError(f"Unknown raw review result: {raw_result}") from exc
