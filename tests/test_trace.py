from delivery_flow.runtime.models import StopReason
from delivery_flow.trace.run_trace import RunTrace


def test_run_trace_records_stage_entries_and_review_outcomes() -> None:
    trace = RunTrace(mode="fallback")

    trace.record_stage_entry("planning")
    trace.record_stage_exit("planning")
    trace.record_task_event(task_id="task-1", event="started")
    trace.record_review(
        raw_result="changes_requested",
        normalized_result="blocker",
        blocker_identity={
            "contract_area": "trace",
            "failure_kind": "missing evidence",
            "expected_resolution": "record state sequence",
        },
    )
    trace.record_issue_action(
        task_id="task-1",
        action="fix_requested",
        summary="trace: missing evidence -> record state sequence",
    )
    trace.record_task_event(task_id="task-1", event="completed")

    assert trace.stage_sequence == ["planning"]
    assert trace.stage_events == [
        {"stage": "planning", "event": "enter"},
        {"stage": "planning", "event": "exit"},
    ]
    assert trace.task_events == [
        {"task_id": "task-1", "event": "started"},
        {"task_id": "task-1", "event": "completed"},
    ]
    assert trace.review_events[0]["normalized_result"] == "blocker"
    assert trace.issue_actions == [
        {
            "task_id": "task-1",
            "action": "fix_requested",
            "summary": "trace: missing evidence -> record state sequence",
        }
    ]


def test_terminal_summary_mentions_delivery_verification_task_issue_and_acceptance_details() -> None:
    trace = RunTrace(mode="superpowers-backed")

    summary = trace.build_terminal_summary(
        delivery_summary="implemented runtime core",
        verification_evidence=["uv run pytest"],
        residual_risk=["broader regression coverage pending"],
        stop_reason=StopReason.NEEDS_OWNER_DECISION,
        completed_task_ids=["task-1"],
        open_issue_summaries=["choose the first real task"],
        owner_acceptance_required=True,
        owner_decision_reason="choose the first real task",
    )

    assert "implemented runtime core" in summary
    assert "uv run pytest" in summary
    assert "needs_owner_decision" in summary
    assert "completed tasks: task-1" in summary
    assert "open issues: choose the first real task" in summary
    assert "owner acceptance required: yes" in summary
    assert "waiting for the owner's next instruction" in summary
    assert trace.final_summary == summary
