from delivery_flow.compatibility import (
    NORMALIZED_REVIEW_SNAPSHOT_VERSION,
    TERMINAL_SUMMARY_SNAPSHOT_VERSION,
    build_normalized_review_snapshot,
    build_terminal_summary_snapshot,
)
from delivery_flow.controller import MainAgentLoopController
from delivery_flow.runtime.models import StopReason
from delivery_flow.trace.run_trace import RunTrace
import pytest


def test_compatibility_snapshot_builders_emit_versioned_serializable_shapes() -> None:
    trace = RunTrace(mode="superpowers-backed")
    summary = trace.build_terminal_summary(
        delivery_summary="implemented runtime core",
        verification_evidence=["uv run pytest"],
        residual_risk=[],
        stop_reason=StopReason.PASS,
    )

    review_snapshot = build_normalized_review_snapshot()
    summary_snapshot = build_terminal_summary_snapshot(
        mode="superpowers-backed",
        stop_reason=StopReason.PASS,
        final_summary=summary,
    )

    assert review_snapshot == {
        "snapshot_version": NORMALIZED_REVIEW_SNAPSHOT_VERSION,
        "normalized_results": {
            "approved": "pass",
            "changes_requested": "blocker",
            "owner_input_required": "needs_owner_decision",
        },
    }
    assert summary_snapshot == {
        "snapshot_version": TERMINAL_SUMMARY_SNAPSHOT_VERSION,
        "mode": "superpowers-backed",
        "stop_reason": "pass",
        "final_summary": summary,
    }


def test_normalized_review_snapshot_delegates_to_controller_normalization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_normalized = {
        "approved": "normalized-approved",
        "changes_requested": "normalized-blocker",
        "owner_input_required": "normalized-owner",
    }
    observed_inputs: list[str] = []

    def fake_normalize_review_result(
        self: MainAgentLoopController,
        raw_result: str,
    ) -> object:
        observed_inputs.append(raw_result)
        return type("NormalizedResult", (), {"value": expected_normalized[raw_result]})()

    monkeypatch.setattr(
        MainAgentLoopController,
        "normalize_review_result",
        fake_normalize_review_result,
    )

    snapshot = build_normalized_review_snapshot()

    assert observed_inputs == [
        "approved",
        "changes_requested",
        "owner_input_required",
    ]
    assert snapshot["normalized_results"] == expected_normalized


def test_compatibility_public_stop_reason_names_are_pinned() -> None:
    assert [stop_reason.value for stop_reason in StopReason] == [
        "pass",
        "needs_owner_decision",
        "same_blocker_after_two_fix_review_cycles",
        "required_verification_cannot_be_completed_with_available_evidence",
    ]


@pytest.mark.parametrize("stop_reason", [stop_reason.value for stop_reason in StopReason])
def test_terminal_summary_snapshot_accepts_serialized_stop_reasons(stop_reason: str) -> None:
    snapshot = build_terminal_summary_snapshot(
        mode="fallback",
        stop_reason=stop_reason,
        final_summary="summary",
    )

    assert snapshot == {
        "snapshot_version": TERMINAL_SUMMARY_SNAPSHOT_VERSION,
        "mode": "fallback",
        "stop_reason": stop_reason,
        "final_summary": "summary",
    }


@pytest.mark.parametrize("stop_reason", list(StopReason))
def test_terminal_summary_snapshot_accepts_enum_stop_reasons(stop_reason: StopReason) -> None:
    snapshot = build_terminal_summary_snapshot(
        mode="fallback",
        stop_reason=stop_reason,
        final_summary="summary",
    )

    assert snapshot == {
        "snapshot_version": TERMINAL_SUMMARY_SNAPSHOT_VERSION,
        "mode": "fallback",
        "stop_reason": stop_reason.value,
        "final_summary": "summary",
    }


@pytest.mark.parametrize(
    "stop_reason",
    [
        "",
        "PASS",
        "unknown",
        "needs-owner-decision",
    ],
)
def test_terminal_summary_snapshot_rejects_invalid_serialized_stop_reasons(stop_reason: str) -> None:
    with pytest.raises(ValueError):
        build_terminal_summary_snapshot(
            mode="fallback",
            stop_reason=stop_reason,
            final_summary="summary",
        )
