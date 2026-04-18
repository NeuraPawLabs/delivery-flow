from types import SimpleNamespace

import pytest

from delivery_flow.contracts import (
    DeliveryArtifact,
    PlanArtifact,
    PlanTaskArtifact,
    RequirementArtifact,
    ReviewArtifact,
    TaskExecutionContext,
)
from delivery_flow.runtime.engine import DeliveryFlowRuntime
from delivery_flow.runtime.models import ControllerState, StopReason


class StubAdapter:
    def discuss_and_spec(self, payload):
        return {"spec_artifact": {"ticket": payload["ticket"]}, "owner_ambiguity": None}

    def plan(self, payload):
        return PlanArtifact(
            summary="runtime plan",
            tasks=[
                PlanTaskArtifact(
                    task_id="task-1",
                    title="Runtime",
                    goal="Implement runtime task",
                    verification_commands=["uv run pytest"],
                )
            ],
        )

    def run_dev(self, payload):
        return {"delivery_summary": "implemented", "verification_evidence": ["pytest"], "residual_risk": []}

    def run_review(self, payload):
        return {"raw_result": "approved", "findings": [], "verification_gaps": []}

    def run_fix(self, payload):
        raise AssertionError("run_fix should not be called in the pass path")

    def finalize(self, payload):
        return {"final_summary": payload}


class ScriptedAdapter(StubAdapter):
    def __init__(self, review_results):
        self._review_results = list(review_results)
        self.fix_calls = 0

    def run_review(self, payload):
        if not self._review_results:
            raise AssertionError("run_review called without scripted review payload")
        return self._review_results.pop(0)

    def run_fix(self, payload):
        self.fix_calls += 1
        assert isinstance(payload, TaskExecutionContext)
        return {
            "delivery_summary": f"fix-{self.fix_calls}",
            "verification_evidence": ["pytest"],
            "residual_risk": [],
            "source_review": payload.latest_review.raw_result if payload.latest_review is not None else None,
        }


class TypedArtifactAdapter:
    def discuss_and_spec(self, payload):
        assert payload == {"ticket": 91, "goal": "typed-runtime"}
        return {"spec_artifact": payload, "owner_ambiguity": None}

    def plan(self, payload):
        return PlanArtifact(
            summary="typed runtime",
            tasks=[
                PlanTaskArtifact(
                    task_id="typed-task",
                    title="Typed runtime",
                    goal="Run typed path",
                    verification_commands=["uv run pytest"],
                )
            ],
        )

    def run_dev(self, payload):
        return DeliveryArtifact(
            delivery_summary="implemented typed path",
            verification_evidence=["uv run pytest"],
            residual_risk=[],
        )

    def run_review(self, payload):
        return ReviewArtifact(raw_result="approved")

    def run_fix(self, payload):
        raise AssertionError("run_fix should not be called in the typed pass path")

    def finalize(self, payload):
        return {"final_summary": payload}


def simulate_path(path_name: str):
    review_results_by_path = {
        "pass": [
            {"raw_result": "approved", "findings": [], "verification_gaps": []},
        ],
        "single_blocker_recovery": [
            {
                "raw_result": "changes_requested",
                "contract_area": "trace",
                "failure_kind": "missing evidence",
                "expected_resolution": "record stage transitions",
            },
            {"raw_result": "approved", "findings": [], "verification_gaps": []},
        ],
        "same_blocker_twice": [
            {
                "raw_result": "changes_requested",
                "contract_area": "stop-rule handling",
                "failure_kind": "incorrect behavior",
                "expected_resolution": "same blocker stops after two cycles",
            },
            {
                "raw_result": "changes_requested",
                "contract_area": "stop-rule handling",
                "failure_kind": "incorrect behavior",
                "expected_resolution": "same blocker stops after two cycles",
            },
            {
                "raw_result": "changes_requested",
                "contract_area": "stop-rule handling",
                "failure_kind": "incorrect behavior",
                "expected_resolution": "same blocker stops after two cycles",
            },
        ],
        "needs_owner_decision": [
            {
                "raw_result": "owner_input_required",
                "findings": ["pick rollout order"],
            },
        ],
        "verification_unavailable": [
            {
                "raw_result": "changes_requested",
                "contract_area": "verification",
                "failure_kind": "",
                "expected_resolution": "supply missing evidence",
            },
        ],
    }

    runtime = DeliveryFlowRuntime(
        adapter=ScriptedAdapter(review_results=review_results_by_path[path_name]),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )
    return runtime.run({"ticket": 90, "goal": path_name})


def test_runtime_pass_path_transitions_into_waiting_for_owner() -> None:
    runtime = DeliveryFlowRuntime(
        adapter=StubAdapter(),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run({"ticket": 86, "goal": "stage-2 runtime"})

    assert result.mode == "superpowers-backed"
    assert result.final_state is ControllerState.WAITING_FOR_OWNER
    assert result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_finalize",
        "waiting_for_owner",
    ]


def test_runtime_rejects_manual_invalid_transition() -> None:
    runtime = DeliveryFlowRuntime(
        adapter=StubAdapter(),
        capability_detector=SimpleNamespace(has_superpowers=False),
    )

    with pytest.raises(RuntimeError, match="Invalid state transition"):
        runtime._transition_to(ControllerState.RUNNING_FIX)


def test_runtime_resets_lifecycle_for_each_run() -> None:
    runtime = DeliveryFlowRuntime(
        adapter=StubAdapter(),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    first_result = runtime.run({"ticket": 86, "goal": "stage-2 runtime"})
    second_result = runtime.run({"ticket": 87, "goal": "stage-2 runtime rerun"})

    assert first_result.final_state is ControllerState.WAITING_FOR_OWNER
    assert second_result.final_state is ControllerState.WAITING_FOR_OWNER
    assert second_result.stage_sequence == [
        "discussing_requirement",
        "writing_spec",
        "planning",
        "running_dev",
        "running_review",
        "running_finalize",
        "waiting_for_owner",
    ]


def test_blocker_path_enters_fix_and_then_passes() -> None:
    adapter = ScriptedAdapter(
        review_results=[
            {
                "raw_result": "changes_requested",
                "findings": ["add runtime trace"],
                "contract_area": "trace",
                "failure_kind": "missing evidence",
                "expected_resolution": "record stage transitions",
            },
            {"raw_result": "approved", "findings": [], "verification_gaps": []},
        ]
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run({"ticket": 87, "goal": "stop rules"})

    assert result.stop_reason is StopReason.PASS
    assert result.final_state is ControllerState.WAITING_FOR_OWNER
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


def test_same_blocker_after_two_fix_review_cycles_stops_runtime() -> None:
    adapter = ScriptedAdapter(
        review_results=[
            {
                "raw_result": "changes_requested",
                "contract_area": "stop-rule handling",
                "failure_kind": "incorrect behavior",
                "expected_resolution": "same blocker stops after two cycles",
            },
            {
                "raw_result": "changes_requested",
                "contract_area": "stop-rule handling",
                "failure_kind": "incorrect behavior",
                "expected_resolution": "same blocker stops after two cycles",
            },
            {
                "raw_result": "changes_requested",
                "contract_area": "stop-rule handling",
                "failure_kind": "incorrect behavior",
                "expected_resolution": "same blocker stops after two cycles",
            },
        ]
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run({"ticket": 87, "goal": "same blocker"})

    assert result.stop_reason is StopReason.SAME_BLOCKER
    assert result.final_state is ControllerState.WAITING_FOR_OWNER
    assert adapter.fix_calls == 2


def test_needs_owner_decision_stops_without_entering_fix() -> None:
    adapter = ScriptedAdapter(
        review_results=[
            {
                "raw_result": "owner_input_required",
                "findings": ["pick rollout order"],
            }
        ]
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=False),
    )

    result = runtime.run({"ticket": 87, "goal": "owner decision"})

    assert result.stop_reason is StopReason.NEEDS_OWNER_DECISION
    assert result.final_state is ControllerState.WAITING_FOR_OWNER
    assert "needs_owner_decision" in result.final_summary
    assert "running_fix" not in result.stage_sequence


def test_missing_blocker_identity_fields_stop_as_verification_unavailable() -> None:
    adapter = ScriptedAdapter(
        review_results=[
            {
                "raw_result": "changes_requested",
                "contract_area": "verification",
                "failure_kind": "",
                "expected_resolution": "supply missing evidence",
            }
        ]
    )
    runtime = DeliveryFlowRuntime(
        adapter=adapter,
        capability_detector=SimpleNamespace(has_superpowers=False),
    )

    result = runtime.run({"ticket": 87, "goal": "verification unavailable"})

    assert result.stop_reason is StopReason.VERIFICATION_UNAVAILABLE
    assert result.final_state is ControllerState.WAITING_FOR_OWNER
    assert "available evidence" in result.final_summary
    assert "running_fix" not in result.stage_sequence


def test_runtime_trace_captures_stage_exits_and_final_summary() -> None:
    runtime = DeliveryFlowRuntime(
        adapter=StubAdapter(),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run({"ticket": 88, "goal": "trace evidence"})

    assert runtime.trace is not None
    assert runtime.trace.final_summary == result.final_summary
    assert {"stage": "running_review", "event": "exit"} in runtime.trace.stage_events
    assert {"stage": "waiting_for_owner", "event": "enter"} in runtime.trace.stage_events


def test_runtime_supports_all_required_terminal_paths() -> None:
    assert simulate_path("pass").stop_reason is StopReason.PASS
    assert simulate_path("single_blocker_recovery").stop_reason is StopReason.PASS
    assert simulate_path("same_blocker_twice").stop_reason is StopReason.SAME_BLOCKER
    assert simulate_path("needs_owner_decision").stop_reason is StopReason.NEEDS_OWNER_DECISION
    assert simulate_path("verification_unavailable").stop_reason is StopReason.VERIFICATION_UNAVAILABLE


def test_runtime_accepts_typed_requirement_and_artifact_payloads() -> None:
    runtime = DeliveryFlowRuntime(
        adapter=TypedArtifactAdapter(),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    result = runtime.run(RequirementArtifact(ticket=91, goal="typed-runtime"))

    assert result.mode == "superpowers-backed"
    assert result.final_state is ControllerState.WAITING_FOR_OWNER
    assert "implemented typed path" in result.final_summary
