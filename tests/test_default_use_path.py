from types import SimpleNamespace

import pytest

from delivery_flow.contracts import TaskExecutionContext
from delivery_flow.controller import run_delivery_flow


class FakeProvider:
    def __init__(self, review_result="approved"):
        self.review_result = review_result

    def discuss_and_spec(self, payload):
        return {"spec_artifact": payload, "owner_ambiguity": None}

    def plan(self, payload):
        return {"plan_artifact": payload}

    def run_dev(self, payload):
        return {
            "delivery_summary": "implemented default path",
            "verification_evidence": ["uv run pytest"],
            "residual_risk": [],
        }

    def run_review(self, payload):
        return {"raw_result": self.review_result, "findings": [], "verification_gaps": []}

    def run_fix(self, payload):
        return {
            "delivery_summary": "fixed finding",
            "verification_evidence": ["uv run pytest"],
            "residual_risk": [],
        }

    def finalize(self, payload):
        return {"final_summary": payload}


def test_run_delivery_flow_defaults_into_runtime_and_emits_mode_banner() -> None:
    result = run_delivery_flow(
        payload={"ticket": 89},
        provider=FakeProvider(),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert result.mode == "superpowers-backed"
    assert result.final_summary.startswith("mode=superpowers-backed")


def test_run_delivery_flow_rejects_missing_capability_detector() -> None:
    with pytest.raises(RuntimeError, match="Capability detector is required"):
        run_delivery_flow(payload={"ticket": 89}, provider=FakeProvider(), capability_detector=None)


class FlakyDetector:
    def __init__(self) -> None:
        self.calls = 0

    @property
    def has_superpowers(self) -> bool:
        self.calls += 1
        return self.calls == 1


def test_run_delivery_flow_freezes_mode_selection_for_runtime_and_adapter() -> None:
    result = run_delivery_flow(
        payload={"ticket": 89},
        provider=FakeProvider(),
        capability_detector=FlakyDetector(),
    )

    assert result.mode == "superpowers-backed"
    assert result.final_summary.startswith("mode=superpowers-backed")


def test_default_use_path_does_not_require_owner_to_restitch_stages() -> None:
    result = run_delivery_flow(
        payload={"ticket": 90, "goal": "default-use path"},
        provider=FakeProvider(review_result="approved"),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_finalize",
        "waiting_for_owner",
    ]
    assert "waiting for the owner's next instruction" in result.final_summary


class TaskLoopProvider:
    def __init__(
        self,
        review_results: list[dict[str, object]],
        *,
        finalize_result: dict[str, object] | None = None,
    ) -> None:
        self.review_results = list(review_results)
        self.finalize_result = finalize_result

    def discuss_and_spec(self, payload):
        return {"spec_artifact": payload, "owner_ambiguity": None}

    def plan(self, payload):
        return {
            "summary": "task-loop default path",
            "tasks": [
                {
                    "task_id": "task-1",
                    "title": "Task 1",
                    "goal": "Execute task-1",
                    "verification_commands": ["uv run pytest"],
                },
                {
                    "task_id": "task-2",
                    "title": "Task 2",
                    "goal": "Execute task-2",
                    "verification_commands": ["uv run pytest"],
                },
            ],
        }

    def run_dev(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        return {
            "delivery_summary": f"implemented {payload.task.task_id}",
            "verification_evidence": [f"pytest {payload.task.task_id}"],
            "residual_risk": [],
        }

    def run_review(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        if not self.review_results:
            raise AssertionError("run_review called without a scripted review result")
        return self.review_results.pop(0)

    def run_fix(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        return {
            "delivery_summary": f"fixed {payload.task.task_id}",
            "verification_evidence": [f"pytest {payload.task.task_id} --fix"],
            "residual_risk": [],
        }

    def finalize(self, payload):
        return self.finalize_result or {"final_summary": payload}


def test_run_delivery_flow_surfaces_task_loop_completion_fields_after_finalize() -> None:
    result = run_delivery_flow(
        payload={"ticket": 91, "goal": "default-use finalize"},
        provider=TaskLoopProvider(
            review_results=[
                {"raw_result": "approved"},
                {"raw_result": "approved"},
            ],
            finalize_result={"owner_acceptance_required": False},
        ),
        capability_detector=SimpleNamespace(has_superpowers=False),
    )

    assert result.mode == "fallback"
    assert result.completed_task_ids == ["task-1", "task-2"]
    assert result.pending_task_id is None
    assert result.open_issue_summaries == []
    assert result.owner_acceptance_required is False
    assert "completed tasks: task-1, task-2" in result.final_summary
    assert "open issues: none" in result.final_summary
    assert "owner acceptance required: no" in result.final_summary


def test_run_delivery_flow_surfaces_pending_task_and_open_issues_when_owner_input_is_required() -> None:
    result = run_delivery_flow(
        payload={"ticket": 92, "goal": "owner decision path"},
        provider=TaskLoopProvider(
            review_results=[
                {"raw_result": "approved"},
                {
                    "raw_result": "owner_input_required",
                    "findings": ["choose rollout order"],
                    "owner_decision_reason": "choose rollout order",
                },
            ]
        ),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert result.mode == "superpowers-backed"
    assert result.completed_task_ids == ["task-1"]
    assert result.pending_task_id == "task-2"
    assert result.open_issue_summaries == ["choose rollout order"]
    assert result.owner_acceptance_required is True
    assert "completed tasks: task-1" in result.final_summary
    assert "open issues: choose rollout order" in result.final_summary
    assert "owner acceptance required: yes" in result.final_summary


def test_run_delivery_flow_surfaces_superpowers_execution_evidence_without_changing_owner_facing_outcome() -> None:
    superpowers_result = run_delivery_flow(
        payload={"ticket": 301, "goal": "orchestration evidence"},
        provider=TaskLoopProvider(
            review_results=[{"raw_result": "approved"}, {"raw_result": "approved"}],
            finalize_result={"owner_acceptance_required": False},
        ),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )
    fallback_result = run_delivery_flow(
        payload={"ticket": 301, "goal": "orchestration evidence"},
        provider=TaskLoopProvider(
            review_results=[{"raw_result": "approved"}, {"raw_result": "approved"}],
            finalize_result={"owner_acceptance_required": False},
        ),
        capability_detector=SimpleNamespace(has_superpowers=False),
    )

    assert superpowers_result.stop_reason == fallback_result.stop_reason
    assert superpowers_result.stage_sequence == fallback_result.stage_sequence
    assert superpowers_result.completed_task_ids == fallback_result.completed_task_ids
    assert superpowers_result.pending_task_id == fallback_result.pending_task_id
    assert superpowers_result.open_issue_summaries == fallback_result.open_issue_summaries
    assert superpowers_result.owner_acceptance_required is fallback_result.owner_acceptance_required is False
    assert (
        "orchestration: backend=superpowers-backed executor_kind=subagent "
        "stages=running_dev,running_review"
    ) in superpowers_result.final_summary
    assert "orchestration:" not in fallback_result.final_summary
    for summary_fragment in (
        "completed tasks: task-1, task-2",
        "open issues: none",
        "owner acceptance required: no",
        "stop reason: pass",
    ):
        assert summary_fragment in superpowers_result.final_summary
        assert summary_fragment in fallback_result.final_summary
    assert "\n".join(superpowers_result.final_summary.splitlines()[1:]) == "\n".join(
        fallback_result.final_summary.splitlines()[1:]
    )
