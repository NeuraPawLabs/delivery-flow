from types import SimpleNamespace

import pytest

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
from delivery_flow.controller import resume_delivery_flow, run_delivery_flow
from delivery_flow.observability.config import resolve_observability_db_path
from delivery_flow.runtime.models import ControllerState, StopReason


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


def test_run_delivery_flow_creates_default_observability_db_when_recorder_is_not_provided(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DELIVERY_FLOW_HOME", str(tmp_path / "global-observability"))

    result = run_delivery_flow(
        payload={"ticket": 90, "goal": "default-use path"},
        provider=FakeProvider(review_result="approved"),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert result.stop_reason is StopReason.PASS
    assert resolve_observability_db_path().is_file()
    assert not (tmp_path / ".delivery_flow" / "observability.db").exists()
    assert (tmp_path / "global-observability" / "observability" / "observability.db").is_file()


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


class ResumeTaskLoopProvider(TaskLoopProvider):
    def __init__(
        self,
        review_results: list[dict[str, object]],
        *,
        finalize_result: dict[str, object] | None = None,
    ) -> None:
        super().__init__(review_results=review_results, finalize_result=finalize_result)
        self.dev_owner_responses: list[str | None] = []
        self.review_owner_responses: list[str | None] = []

    def run_dev(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        self.dev_owner_responses.append(payload.owner_response)
        return super().run_dev(payload)

    def run_review(self, payload):
        assert isinstance(payload, TaskExecutionContext)
        self.review_owner_responses.append(payload.owner_response)
        return super().run_review(payload)


def _resume_request(*, mode: str, restart_current_task_from_dev: bool = False) -> ResumeRequestArtifact:
    plan = PlanArtifact(
        summary="task-loop default path",
        tasks=[
            PlanTaskArtifact(
                task_id="task-1",
                title="Task 1",
                goal="Execute task-1",
                verification_commands=["uv run pytest"],
            ),
            PlanTaskArtifact(
                task_id="task-2",
                title="Task 2",
                goal="Execute task-2",
                verification_commands=["uv run pytest"],
            ),
        ],
    )
    return ResumeRequestArtifact(
        previous_result=RuntimeResult(
            mode=mode,
            final_state=ControllerState.WAITING_FOR_OWNER,
            stop_reason=StopReason.NEEDS_OWNER_DECISION,
            stage_sequence=[
                "discussing_requirement",
                "writing_spec",
                "planning",
                "running_dev",
                "running_review",
                "running_dev",
                "running_review",
                "waiting_for_owner",
            ],
            completed_task_ids=["task-1"],
            pending_task_id="task-2",
            open_issue_summaries=["choose rollout order"],
            resume_context=ResumeContextArtifact(
                plan=plan,
                task_index=1,
                latest_delivery=DeliveryArtifact(delivery_summary="implemented task-2"),
                latest_review=ReviewArtifact(
                    raw_result="owner_input_required",
                    findings=["choose rollout order"],
                    owner_decision_reason="choose rollout order",
                ),
            ),
        ),
        owner_response="roll out to canary first",
        restart_current_task_from_dev=restart_current_task_from_dev,
    )


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


def test_resume_delivery_flow_defaults_to_current_task_review() -> None:
    provider = ResumeTaskLoopProvider(
        review_results=[{"raw_result": "approved"}],
        finalize_result={"owner_acceptance_required": False},
    )

    result = resume_delivery_flow(
        request=_resume_request(mode="superpowers-backed"),
        provider=provider,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert result.stop_reason is StopReason.PASS
    assert provider.dev_owner_responses == []
    assert provider.review_owner_responses == ["roll out to canary first"]
    assert result.completed_task_ids == ["task-1", "task-2"]
    assert result.pending_task_id is None
    assert result.open_issue_summaries == []
    assert result.owner_acceptance_required is False


def test_resume_delivery_flow_can_restart_current_task_from_dev() -> None:
    provider = ResumeTaskLoopProvider(
        review_results=[{"raw_result": "approved"}],
        finalize_result={"owner_acceptance_required": False},
    )

    result = resume_delivery_flow(
        request=_resume_request(mode="superpowers-backed", restart_current_task_from_dev=True),
        provider=provider,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert result.stop_reason is StopReason.PASS
    assert provider.dev_owner_responses == ["roll out to canary first"]
    assert provider.review_owner_responses == ["roll out to canary first"]
    assert result.completed_task_ids == ["task-1", "task-2"]
    assert result.pending_task_id is None
    assert result.open_issue_summaries == []
    assert result.owner_acceptance_required is False
