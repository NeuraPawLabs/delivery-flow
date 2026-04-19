from types import SimpleNamespace

from delivery_flow.contracts import (
    DeliveryArtifact,
    PlanArtifact,
    PlanTaskArtifact,
    ResumeContextArtifact,
    ResumeRequestArtifact,
    ReviewArtifact,
    RuntimeResult,
    TaskExecutionContext,
)
from delivery_flow.runtime.engine import DeliveryFlowRuntime
from delivery_flow.runtime.models import ControllerState, StopReason


def _plan(*task_ids: str) -> PlanArtifact:
    return PlanArtifact(
        summary="task loop runtime",
        tasks=[
            PlanTaskArtifact(
                task_id=task_id,
                title=f"Task {index + 1}",
                goal=f"Execute {task_id}",
                verification_commands=["uv run pytest"],
            )
            for index, task_id in enumerate(task_ids)
        ],
    )


class TaskLoopAdapter:
    def __init__(
        self,
        plan: PlanArtifact,
        review_results: list[dict[str, object]],
        *,
        finalize_result: dict[str, object] | None = None,
        emit_execution_metadata: bool = False,
    ) -> None:
        self.plan_artifact = plan
        self.review_results = list(review_results)
        self.finalize_result = finalize_result
        self.emit_execution_metadata = emit_execution_metadata
        self.dev_calls: list[str] = []
        self.review_calls: list[str] = []
        self.fix_calls: list[str] = []
        self.finalize_calls = 0

    def discuss_and_spec(self, payload):
        return {"spec_artifact": payload, "owner_ambiguity": None}

    def plan(self, payload):
        return self.plan_artifact

    def _execution_metadata(self, stage: str) -> dict[str, str] | None:
        if not self.emit_execution_metadata:
            return None

        return {
            "stage": stage,
            "backend": "superpowers-backed",
            "executor_kind": "subagent",
        }

    def run_dev(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        self.dev_calls.append(payload.task.task_id)
        result = {
            "delivery_summary": f"implemented {payload.task.task_id}",
            "verification_evidence": [f"pytest {payload.task.task_id}"],
            "residual_risk": [],
        }
        execution_metadata = self._execution_metadata("running_dev")
        if execution_metadata is not None:
            result["execution_metadata"] = execution_metadata
        return result

    def run_review(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        self.review_calls.append(payload.task.task_id)
        if not self.review_results:
            raise AssertionError("run_review called without a scripted review result")
        result = dict(self.review_results.pop(0))
        execution_metadata = self._execution_metadata("running_review")
        if execution_metadata is not None:
            result.setdefault("execution_metadata", execution_metadata)
        return result

    def run_fix(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        self.fix_calls.append(payload.task.task_id)
        result = {
            "delivery_summary": f"fixed {payload.task.task_id}",
            "verification_evidence": [f"pytest {payload.task.task_id} --fix"],
            "residual_risk": [],
        }
        execution_metadata = self._execution_metadata("running_fix")
        if execution_metadata is not None:
            result["execution_metadata"] = execution_metadata
        return result

    def finalize(self, payload):
        self.finalize_calls += 1
        return dict(self.finalize_result or {"final_summary": payload})


def test_runtime_advances_to_next_task_after_task_pass_without_stopping() -> None:
    adapter = TaskLoopAdapter(
        plan=_plan("task-1", "task-2"),
        review_results=[
            {"raw_result": "approved"},
            {"raw_result": "approved"},
        ],
        finalize_result={"owner_acceptance_required": False},
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run({"ticket": 201, "goal": "advance tasks"})

    assert result.stop_reason is StopReason.PASS
    assert result.final_state is ControllerState.WAITING_FOR_OWNER
    assert adapter.dev_calls == ["task-1", "task-2"]
    assert adapter.review_calls == ["task-1", "task-2"]
    assert adapter.fix_calls == []
    assert adapter.finalize_calls == 1
    assert result.completed_task_ids == ["task-1", "task-2"]
    assert result.pending_task_id is None
    assert result.open_issue_summaries == []
    assert result.owner_acceptance_required is False
    assert result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_dev",
        "running_review",
        "running_finalize",
        "waiting_for_owner",
    ]
    assert "completed tasks: task-1, task-2" in result.final_summary
    assert "open issues: none" in result.final_summary
    assert "owner acceptance required: no" in result.final_summary
    assert runtime.trace is not None
    assert runtime.trace.task_events == [
        {"task_id": "task-1", "event": "started"},
        {"task_id": "task-1", "event": "completed"},
        {"task_id": "task-2", "event": "started"},
        {"task_id": "task-2", "event": "completed"},
    ]


def test_runtime_loops_fix_review_within_one_task_until_pass() -> None:
    adapter = TaskLoopAdapter(
        plan=_plan("task-1"),
        review_results=[
            {
                "raw_result": "changes_requested",
                "contract_area": "runtime",
                "failure_kind": "missing transition",
                "expected_resolution": "re-enter review after fix",
            },
            {"raw_result": "approved"},
        ],
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run({"ticket": 202, "goal": "fix review loop"})

    assert result.stop_reason is StopReason.PASS
    assert adapter.dev_calls == ["task-1"]
    assert adapter.review_calls == ["task-1", "task-1"]
    assert adapter.fix_calls == ["task-1"]
    assert result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_fix",
        "running_review",
        "running_finalize",
        "waiting_for_owner",
    ]


def test_same_blocker_escalation_is_scoped_to_one_task() -> None:
    adapter = TaskLoopAdapter(
        plan=_plan("task-1", "task-2"),
        review_results=[
            {
                "raw_result": "changes_requested",
                "contract_area": "runtime",
                "failure_kind": "issue-a",
                "expected_resolution": "fix issue a",
            },
            {
                "raw_result": "changes_requested",
                "contract_area": "runtime",
                "failure_kind": "issue-b",
                "expected_resolution": "fix issue b",
            },
            {
                "raw_result": "changes_requested",
                "contract_area": "runtime",
                "failure_kind": "issue-b",
                "expected_resolution": "fix issue b",
            },
            {"raw_result": "approved"},
            {
                "raw_result": "changes_requested",
                "contract_area": "runtime",
                "failure_kind": "issue-b",
                "expected_resolution": "fix issue b",
            },
            {"raw_result": "approved"},
        ],
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run({"ticket": 203, "goal": "scope blockers per task"})

    assert result.stop_reason is StopReason.PASS
    assert adapter.dev_calls == ["task-1", "task-2"]
    assert adapter.fix_calls == ["task-1", "task-1", "task-1", "task-2"]
    assert adapter.finalize_calls == 1


def test_approved_review_with_strict_pass_issues_is_downgraded_to_blocker() -> None:
    adapter = TaskLoopAdapter(
        plan=_plan("task-1"),
        review_results=[
            {
                "raw_result": "approved",
                "required_changes": ["rename helper"],
                "testing_issues": ["add regression test"],
                "maintainability_issues": ["remove duplicate branch"],
            },
            {"raw_result": "approved"},
        ],
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run({"ticket": 204, "goal": "downgrade strict pass"})

    assert result.stop_reason is StopReason.PASS
    assert adapter.fix_calls == ["task-1"]
    assert runtime.trace is not None
    assert runtime.trace.review_events[0]["normalized_result"] == "blocker"
    assert runtime.trace.review_events[0]["blocker_identity"] == {
        "contract_area": "review",
        "failure_kind": "required_changes, testing_issues, maintainability_issues",
        "expected_resolution": "resolve strict pass review issues before continuing",
    }


def test_runtime_surfaces_pending_task_open_issues_and_issue_actions_when_owner_input_is_required() -> None:
    adapter = TaskLoopAdapter(
        plan=_plan("task-1", "task-2"),
        review_results=[
            {"raw_result": "approved"},
            {
                "raw_result": "owner_input_required",
                "findings": ["choose rollout order"],
                "owner_decision_reason": "choose rollout order",
            },
        ],
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run({"ticket": 205, "goal": "surface task loop evidence"})

    assert result.stop_reason is StopReason.NEEDS_OWNER_DECISION
    assert result.completed_task_ids == ["task-1"]
    assert result.pending_task_id == "task-2"
    assert result.open_issue_summaries == ["choose rollout order"]
    assert result.owner_acceptance_required is True
    assert "completed tasks: task-1" in result.final_summary
    assert "open issues: choose rollout order" in result.final_summary
    assert "owner acceptance required: yes" in result.final_summary
    assert runtime.trace is not None
    assert runtime.trace.task_events == [
        {"task_id": "task-1", "event": "started"},
        {"task_id": "task-1", "event": "completed"},
        {"task_id": "task-2", "event": "started"},
    ]
    assert runtime.trace.issue_actions == [
        {
            "task_id": "task-2",
            "action": "owner_decision_required",
            "summary": "choose rollout order",
        }
    ]


def test_runtime_surfaces_compact_orchestration_evidence_without_changing_task_loop_semantics() -> None:
    adapter = TaskLoopAdapter(
        plan=_plan("task-1"),
        review_results=[
            {
                "raw_result": "changes_requested",
                "contract_area": "runtime",
                "failure_kind": "missing transition",
                "expected_resolution": "re-enter review after fix",
            },
            {"raw_result": "approved"},
        ],
        emit_execution_metadata=True,
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run({"ticket": 206, "goal": "trace compact orchestration evidence"})

    assert result.stop_reason is StopReason.PASS
    assert adapter.dev_calls == ["task-1"]
    assert adapter.review_calls == ["task-1", "task-1"]
    assert adapter.fix_calls == ["task-1"]
    assert result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_fix",
        "running_review",
        "running_finalize",
        "waiting_for_owner",
    ]
    assert "completed tasks: task-1" in result.final_summary
    assert "open issues: none" in result.final_summary
    assert "owner acceptance required: yes" in result.final_summary
    assert (
        "orchestration: backend=superpowers-backed executor_kind=subagent "
        "stages=running_dev,running_review,running_fix"
    ) in result.final_summary
    assert runtime.trace is not None
    assert (
        runtime.trace.execution_summary()
        == "backend=superpowers-backed executor_kind=subagent "
        "stages=running_dev,running_review,running_fix"
    )
    assert runtime.trace.task_events == [
        {"task_id": "task-1", "event": "started"},
        {"task_id": "task-1", "event": "completed"},
    ]
    assert runtime.trace.issue_actions == [
        {
            "task_id": "task-1",
            "action": "fix_requested",
            "summary": "runtime: missing transition -> re-enter review after fix",
        }
    ]


def test_resume_continues_remaining_tasks_after_current_task_review_passes() -> None:
    adapter = TaskLoopAdapter(
        plan=_plan("task-1", "task-2"),
        review_results=[
            {"raw_result": "approved"},
            {"raw_result": "approved"},
        ],
        finalize_result={"owner_acceptance_required": False},
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.resume(
        ResumeRequestArtifact(
            previous_result=RuntimeResult(
                mode="superpowers-backed",
                final_state=ControllerState.WAITING_FOR_OWNER,
                stage_sequence=[
                    "discussing_requirement",
                    "writing_spec",
                    "planning",
                    "running_dev",
                    "running_review",
                    "waiting_for_owner",
                ],
                stop_reason=StopReason.NEEDS_OWNER_DECISION,
                completed_task_ids=[],
                pending_task_id="task-1",
                resume_context=ResumeContextArtifact(
                    plan=_plan("task-1", "task-2"),
                    task_index=0,
                    latest_delivery=DeliveryArtifact(delivery_summary="implemented task-1"),
                    latest_review=ReviewArtifact(
                        raw_result="owner_input_required",
                        findings=["choose rollout order"],
                        owner_decision_reason="choose rollout order",
                    ),
                ),
            ),
            owner_response="task-1 can proceed",
        )
    )

    assert result.stop_reason is StopReason.PASS
    assert adapter.dev_calls == ["task-2"]
    assert adapter.review_calls == ["task-1", "task-2"]
    assert adapter.fix_calls == []
    assert result.completed_task_ids == ["task-1", "task-2"]
    assert result.pending_task_id is None
    assert result.owner_acceptance_required is False


def test_runtime_surfaces_fallback_open_issue_summary_for_verification_unavailable() -> None:
    adapter = TaskLoopAdapter(
        plan=_plan("task-1", "task-2"),
        review_results=[
            {"raw_result": "approved"},
            {
                "raw_result": "changes_requested",
                "contract_area": "runtime",
            },
        ],
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run({"ticket": 206, "goal": "surface verification unavailable evidence"})

    assert result.stop_reason is StopReason.VERIFICATION_UNAVAILABLE
    assert result.completed_task_ids == ["task-1"]
    assert result.pending_task_id == "task-2"
    assert result.open_issue_summaries == [
        "review blocker identity incomplete: missing failure_kind, expected_resolution"
    ]
    assert "open issues: review blocker identity incomplete: missing failure_kind, expected_resolution" in result.final_summary
    assert runtime.trace is not None
    assert runtime.trace.issue_actions == [
        {
            "task_id": "task-2",
            "action": "verification_unavailable",
            "summary": "review blocker identity incomplete: missing failure_kind, expected_resolution",
        }
    ]
