from types import SimpleNamespace

from delivery_flow.contracts import PlanArtifact, PlanTaskArtifact, TaskExecutionContext
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
    def __init__(self, plan: PlanArtifact, review_results: list[dict[str, object]]) -> None:
        self.plan_artifact = plan
        self.review_results = list(review_results)
        self.dev_calls: list[str] = []
        self.review_calls: list[str] = []
        self.fix_calls: list[str] = []
        self.finalize_calls = 0

    def discuss_and_spec(self, payload):
        return {"spec_artifact": payload, "owner_ambiguity": None}

    def plan(self, payload):
        return self.plan_artifact

    def run_dev(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        self.dev_calls.append(payload.task.task_id)
        return {
            "delivery_summary": f"implemented {payload.task.task_id}",
            "verification_evidence": [f"pytest {payload.task.task_id}"],
            "residual_risk": [],
        }

    def run_review(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        self.review_calls.append(payload.task.task_id)
        if not self.review_results:
            raise AssertionError("run_review called without a scripted review result")
        return self.review_results.pop(0)

    def run_fix(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        self.fix_calls.append(payload.task.task_id)
        return {
            "delivery_summary": f"fixed {payload.task.task_id}",
            "verification_evidence": [f"pytest {payload.task.task_id} --fix"],
            "residual_risk": [],
        }

    def finalize(self, payload):
        self.finalize_calls += 1
        return {"final_summary": payload}


def test_runtime_advances_to_next_task_after_task_pass_without_stopping() -> None:
    adapter = TaskLoopAdapter(
        plan=_plan("task-1", "task-2"),
        review_results=[
            {"raw_result": "approved"},
            {"raw_result": "approved"},
        ],
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
