from __future__ import annotations

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
from delivery_flow.controller import resume_delivery_flow, run_delivery_flow
from delivery_flow.observability.recorder import build_sqlite_recorder
from delivery_flow.runtime.engine import DeliveryFlowRuntime
from delivery_flow.runtime.models import ControllerState, StopReason


def _plan(*task_ids: str) -> PlanArtifact:
    return PlanArtifact(
        summary="observability runtime",
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
    ) -> None:
        self.plan_artifact = plan
        self.review_results = list(review_results)
        self.finalize_result = finalize_result

    def discuss_and_spec(self, payload):
        return {"spec_artifact": payload, "owner_ambiguity": None}

    def plan(self, payload):
        return self.plan_artifact

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


class FakeProvider:
    def __init__(self, review_result: str = "approved") -> None:
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


class ResumeProvider(FakeProvider):
    def __init__(self) -> None:
        self.review_owner_responses: list[str | None] = []

    def run_review(self, payload):
        self.review_owner_responses.append(payload.owner_response)
        return {"raw_result": "approved", "findings": [], "verification_gaps": []}


def test_runtime_persists_task_dispatch_loop_and_review_records(tmp_path) -> None:
    recorder = build_sqlite_recorder(
        db_path=tmp_path / "observability.sqlite3",
        project_root=tmp_path,
        skill_name="delivery-flow",
    )
    adapter = TaskLoopAdapter(
        plan=_plan("task-1"),
        review_results=[
            {
                "raw_result": "changes_requested",
                "contract_area": "runtime",
                "failure_kind": "missing test",
                "expected_resolution": "add missing test",
            },
            {"raw_result": "approved"},
        ],
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
        recorder=recorder,
    )

    result = runtime.run({"ticket": 401, "goal": "persist observability"})
    snapshot = recorder.query_debug_snapshot()
    first_loop = snapshot["task_loops"][0]
    second_loop = snapshot["task_loops"][1]
    first_dispatch = snapshot["task_dispatches"][0]
    second_dispatch = snapshot["task_dispatches"][1]

    assert result.stop_reason is StopReason.PASS
    assert snapshot["runs"][0]["stop_reason"] == "pass"
    assert snapshot["tasks"][0]["task_id"] == "task-1"
    assert snapshot["task_dispatches"][0]["selected_stage"] == "running_dev"
    assert [
        (row["task_id"], row["loop_index"], row["final_review_result"])
        for row in snapshot["task_loops"]
    ] == [
        ("task-1", 1, "blocker"),
        ("task-1", 2, "pass"),
    ]
    assert [event["event_kind"] for event in snapshot["events"]] == [
        "run_started",
        "task_registered",
        "task_loop_started",
        "task_dispatched",
        "review_recorded",
        "task_loop_started",
        "task_dispatched",
        "review_recorded",
        "run_completed",
    ]
    assert snapshot["events"][2]["loop_id"] == first_loop["loop_id"]
    assert snapshot["events"][2]["dispatch_id"] is None
    assert snapshot["events"][3]["loop_id"] == first_dispatch["loop_id"] == first_loop["loop_id"]
    assert snapshot["events"][3]["dispatch_id"] == first_dispatch["dispatch_id"]
    assert snapshot["events"][4]["loop_id"] == first_loop["loop_id"]
    assert snapshot["events"][4]["dispatch_id"] == first_dispatch["dispatch_id"]
    assert snapshot["events"][5]["loop_id"] == second_loop["loop_id"]
    assert snapshot["events"][5]["dispatch_id"] is None
    assert snapshot["events"][6]["loop_id"] == second_dispatch["loop_id"] == second_loop["loop_id"]
    assert snapshot["events"][6]["dispatch_id"] == second_dispatch["dispatch_id"]
    assert second_dispatch["selected_stage"] == "running_fix"
    assert snapshot["events"][6]["loop_id"] == second_loop["loop_id"]
    assert snapshot["events"][7]["dispatch_id"] == second_dispatch["dispatch_id"]


def test_run_delivery_flow_owner_facing_result_is_unchanged_when_recorder_is_enabled(tmp_path) -> None:
    result = run_delivery_flow(
        payload={"ticket": 402, "goal": "observability parity"},
        provider=FakeProvider(review_result="approved"),
        capability_detector=SimpleNamespace(has_superpowers=True),
        recorder=build_sqlite_recorder(
            db_path=tmp_path / "observability.sqlite3",
            project_root=tmp_path,
            skill_name="delivery-flow",
        ),
    )

    assert result.mode == "superpowers-backed"
    assert result.stop_reason is StopReason.PASS
    assert result.final_summary.startswith("mode=superpowers-backed")


def test_resume_delivery_flow_persists_observability_when_recorder_is_enabled(tmp_path) -> None:
    recorder = build_sqlite_recorder(
        db_path=tmp_path / "observability.sqlite3",
        project_root=tmp_path,
        skill_name="delivery-flow",
    )
    provider = ResumeProvider()
    plan = _plan("task-1")

    result = resume_delivery_flow(
        request=ResumeRequestArtifact(
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
                final_summary="waiting for owner",
                completed_task_ids=[],
                pending_task_id="task-1",
                open_issue_summaries=["pick rollout order"],
                owner_acceptance_required=True,
                resume_context=ResumeContextArtifact(
                    plan=plan,
                    task_index=0,
                    latest_delivery=DeliveryArtifact(delivery_summary="implemented task-1"),
                    latest_review=ReviewArtifact(
                        raw_result="owner_input_required",
                        findings=["pick rollout order"],
                        owner_decision_reason="pick rollout order",
                    ),
                ),
            ),
            owner_response="ship canary first",
        ),
        provider=provider,
        capability_detector=SimpleNamespace(has_superpowers=True),
        recorder=recorder,
    )
    snapshot = recorder.query_debug_snapshot()

    assert result.stop_reason is StopReason.PASS
    assert provider.review_owner_responses == ["ship canary first"]
    assert len(snapshot["runs"]) == 1
    assert snapshot["runs"][0]["mode"] == "superpowers-backed"
    assert snapshot["runs"][0]["stop_reason"] == "pass"
    assert [row["task_id"] for row in snapshot["tasks"]] == ["task-1"]
    assert [event["event_kind"] for event in snapshot["events"]] == [
        "run_started",
        "task_registered",
        "task_loop_started",
        "task_dispatched",
        "review_recorded",
        "run_completed",
    ]
    assert snapshot["events"][2]["loop_id"] == snapshot["task_loops"][0]["loop_id"]
    assert snapshot["events"][3]["dispatch_id"] == snapshot["task_dispatches"][0]["dispatch_id"]
    assert snapshot["events"][4]["dispatch_id"] == snapshot["task_dispatches"][0]["dispatch_id"]


def test_runtime_persists_review_record_for_verification_unavailable_path(tmp_path) -> None:
    recorder = build_sqlite_recorder(
        db_path=tmp_path / "observability.sqlite3",
        project_root=tmp_path,
        skill_name="delivery-flow",
    )
    adapter = TaskLoopAdapter(
        plan=_plan("task-1"),
        review_results=[
            {
                "raw_result": "changes_requested",
                "findings": ["missing blocker identity"],
            }
        ],
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
        recorder=recorder,
    )

    result = runtime.run({"ticket": 403, "goal": "persist verification unavailable review"})
    snapshot = recorder.query_debug_snapshot()

    assert result.stop_reason is StopReason.VERIFICATION_UNAVAILABLE
    assert snapshot["task_loops"] == [
        {
            "loop_id": snapshot["task_loops"][0]["loop_id"],
            "task_id": "task-1",
            "loop_index": 1,
            "final_review_result": "blocker",
        }
    ]
    assert [event["event_kind"] for event in snapshot["events"]] == [
        "run_started",
        "task_registered",
        "task_loop_started",
        "task_dispatched",
        "review_recorded",
        "run_completed",
    ]
