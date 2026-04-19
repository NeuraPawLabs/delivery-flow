import pytest

import delivery_flow.contracts as contracts
from delivery_flow.contracts import DeliveryArtifact
from delivery_flow.contracts.models import ExecutionMetadata, ReviewArtifact
from delivery_flow.runtime.models import StopReason
from delivery_flow.trace.run_trace import RunTrace


def test_contract_package_does_not_re_export_execution_metadata() -> None:
    assert not hasattr(contracts, "ExecutionMetadata")


def test_delivery_artifact_accepts_optional_execution_metadata() -> None:
    artifact = DeliveryArtifact(
        delivery_summary="implemented runtime core",
        execution_metadata=ExecutionMetadata(
            stage="running_dev",
            backend="superpowers-backed",
            executor_kind="subagent",
        ),
    )

    assert artifact.execution_metadata == ExecutionMetadata(
        stage="running_dev",
        backend="superpowers-backed",
        executor_kind="subagent",
    )


def test_review_artifact_accepts_optional_execution_metadata() -> None:
    artifact = ReviewArtifact(
        raw_result="approved",
        execution_metadata=ExecutionMetadata(
            stage="running_review",
            backend="superpowers-backed",
            executor_kind="subagent",
        ),
    )

    assert artifact.execution_metadata == ExecutionMetadata(
        stage="running_review",
        backend="superpowers-backed",
        executor_kind="subagent",
    )
def test_execution_metadata_requires_complete_values() -> None:
    with pytest.raises(ValueError, match="complete"):
        ExecutionMetadata(
            stage="running_dev",
            backend="",
            executor_kind="subagent",
        )


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


def test_run_trace_records_stage_entries_review_outcomes_and_execution_metadata() -> None:
    trace = RunTrace(mode="superpowers-backed")

    trace.record_stage_entry("running_dev")
    trace.record_execution(
        stage="running_dev",
        backend="superpowers-backed",
        executor_kind="subagent",
    )

    assert trace.execution_events == [
        ExecutionMetadata(
            stage="running_dev",
            backend="superpowers-backed",
            executor_kind="subagent",
        )
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


def test_run_trace_builds_compact_orchestration_summary_when_execution_metadata_exists() -> None:
    trace = RunTrace(mode="superpowers-backed")
    trace.record_execution(
        stage="running_dev",
        backend="superpowers-backed",
        executor_kind="subagent",
    )
    trace.record_execution(
        stage="running_review",
        backend="superpowers-backed",
        executor_kind="subagent",
    )
    trace.record_execution(
        stage="running_review",
        backend="superpowers-backed",
        executor_kind="subagent",
    )

    assert (
        trace.execution_summary()
        == "backend=superpowers-backed executor_kind=subagent stages=running_dev,running_review"
    )


def test_terminal_summary_mentions_compact_orchestration_evidence_when_execution_metadata_exists() -> None:
    trace = RunTrace(mode="superpowers-backed")
    trace.record_execution(
        stage="running_dev",
        backend="superpowers-backed",
        executor_kind="subagent",
    )
    trace.record_execution(
        stage="running_review",
        backend="superpowers-backed",
        executor_kind="subagent",
    )

    summary = trace.build_terminal_summary(
        delivery_summary="implemented runtime core",
        verification_evidence=["uv run pytest"],
        residual_risk=[],
        stop_reason=StopReason.PASS,
        owner_acceptance_required=True,
    )

    assert (
        "orchestration: backend=superpowers-backed executor_kind=subagent "
        "stages=running_dev,running_review"
    ) in summary
