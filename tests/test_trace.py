from delivery_flow.runtime.models import StopReason
from delivery_flow.trace.run_trace import RunTrace


def test_run_trace_records_stage_entries_and_review_outcomes() -> None:
    trace = RunTrace(mode="fallback")

    trace.record_stage_entry("planning")
    trace.record_stage_exit("planning")
    trace.record_review(
        raw_result="changes_requested",
        normalized_result="blocker",
        blocker_identity={
            "contract_area": "trace",
            "failure_kind": "missing evidence",
            "expected_resolution": "record state sequence",
        },
    )

    assert trace.stage_sequence == ["planning"]
    assert trace.stage_events == [
        {"stage": "planning", "event": "enter"},
        {"stage": "planning", "event": "exit"},
    ]
    assert trace.review_events[0]["normalized_result"] == "blocker"


def test_terminal_summary_mentions_delivery_verification_stop_reason_and_waiting() -> None:
    trace = RunTrace(mode="superpowers-backed")

    summary = trace.build_terminal_summary(
        delivery_summary="implemented runtime core",
        verification_evidence=["uv run pytest"],
        residual_risk=["real-task validation pending"],
        stop_reason=StopReason.NEEDS_OWNER_DECISION,
        owner_decision_reason="choose the first real task",
    )

    assert "implemented runtime core" in summary
    assert "uv run pytest" in summary
    assert "needs_owner_decision" in summary
    assert "waiting for the owner's next instruction" in summary
    assert trace.final_summary == summary
