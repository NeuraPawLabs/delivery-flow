from __future__ import annotations

from delivery_flow.controller import MainAgentLoopController
from delivery_flow.runtime.models import StopReason

NORMALIZED_REVIEW_SNAPSHOT_VERSION = "1.0"
TERMINAL_SUMMARY_SNAPSHOT_VERSION = "1.0"


def build_normalized_review_snapshot() -> dict[str, object]:
    controller = MainAgentLoopController()
    normalized_results = {
        raw_result: controller.normalize_review_result(raw_result).value
        for raw_result in (
            "approved",
            "changes_requested",
            "owner_input_required",
        )
    }
    return {
        "snapshot_version": NORMALIZED_REVIEW_SNAPSHOT_VERSION,
        "normalized_results": normalized_results,
    }


def build_terminal_summary_snapshot(
    *,
    mode: str,
    stop_reason: StopReason | str,
    final_summary: str,
) -> dict[str, str]:
    if isinstance(stop_reason, StopReason):
        serialized_stop_reason = stop_reason.value
    else:
        serialized_stop_reason = StopReason(stop_reason).value
    return {
        "snapshot_version": TERMINAL_SUMMARY_SNAPSHOT_VERSION,
        "mode": mode,
        "stop_reason": serialized_stop_reason,
        "final_summary": final_summary,
    }
