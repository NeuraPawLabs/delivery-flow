from types import SimpleNamespace

import delivery_flow
import delivery_flow.controller as controller_module
import delivery_flow.contracts as contracts_module
import delivery_flow.runtime.engine as runtime_engine_module
import delivery_flow.runtime.models as runtime_models_module
import pytest
from delivery_flow import (
    CONTRACT_SCHEMA_VERSION,
    DeliveryArtifact,
    MainAgentLoopController,
    ResumeContextArtifact,
    ResumeRequestArtifact,
    RequirementArtifact,
    ReviewArtifact,
    RuntimeResult,
    resume_delivery_flow,
    run_delivery_flow,
)
from delivery_flow.runtime import (
    BlockerIdentity,
    ControllerState,
    DeliveryFlowRuntime,
    NormalizedReviewResult,
    RuntimeResult as RuntimePackageResult,
    StopReason,
)
from delivery_flow.contracts import PlanArtifact, PlanTaskArtifact


def test_top_level_package_exports_stable_public_contracts() -> None:
    assert delivery_flow.__all__ == [
        "CONTRACT_SCHEMA_VERSION",
        "DeliveryArtifact",
        "ResumeContextArtifact",
        "ResumeRequestArtifact",
        "RequirementArtifact",
        "ReviewArtifact",
        "RuntimeResult",
        "MainAgentLoopController",
        "resume_delivery_flow",
        "run_delivery_flow",
    ]
    assert callable(run_delivery_flow)
    assert ResumeContextArtifact is contracts_module.ResumeContextArtifact
    assert ResumeRequestArtifact is contracts_module.ResumeRequestArtifact
    assert DeliveryArtifact is contracts_module.DeliveryArtifact
    assert MainAgentLoopController is controller_module.MainAgentLoopController
    assert RequirementArtifact is contracts_module.RequirementArtifact
    assert ReviewArtifact is contracts_module.ReviewArtifact
    assert RuntimeResult is contracts_module.RuntimeResult
    assert resume_delivery_flow is controller_module.resume_delivery_flow
    assert run_delivery_flow is controller_module.run_delivery_flow


def test_top_level_package_does_not_export_compatibility_helpers() -> None:
    assert CONTRACT_SCHEMA_VERSION == contracts_module.CONTRACT_SCHEMA_VERSION
    assert not hasattr(delivery_flow, "build_normalized_review_snapshot")
    assert not hasattr(delivery_flow, "build_terminal_summary_snapshot")
    assert "build_normalized_review_snapshot" not in delivery_flow.__all__
    assert "build_terminal_summary_snapshot" not in delivery_flow.__all__


def test_top_level_package_keeps_observability_internal() -> None:
    assert "observability" not in delivery_flow.__all__
    assert "build_sqlite_recorder" not in delivery_flow.__all__
    assert "ObservabilityRecorder" not in delivery_flow.__all__
    assert not hasattr(delivery_flow, "ObservabilityRecorder")
    assert not hasattr(delivery_flow, "ObservabilityApp")
    assert not hasattr(delivery_flow, "build_sqlite_recorder")
    assert not hasattr(delivery_flow, "build_observability_app")
    namespace: dict[str, object] = {}
    exec("from delivery_flow import *", {}, namespace)
    assert "observability" not in namespace
    assert "build_sqlite_recorder" not in namespace
    assert "ObservabilityRecorder" not in namespace


def test_top_level_package_exports_resume_entry_point() -> None:
    assert "resume_delivery_flow" in delivery_flow.__all__
    assert callable(resume_delivery_flow)


def test_runtime_package_exports_stable_symbols() -> None:
    assert DeliveryFlowRuntime is runtime_engine_module.DeliveryFlowRuntime
    assert ControllerState is runtime_models_module.ControllerState
    assert NormalizedReviewResult is runtime_models_module.NormalizedReviewResult
    assert RuntimePackageResult is contracts_module.RuntimeResult
    assert StopReason is runtime_models_module.StopReason
    assert BlockerIdentity is runtime_models_module.BlockerIdentity


def test_contracts_package_exports_task_loop_contract_symbols() -> None:
    assert contracts_module.__all__ == [
        "BlockerIdentityPayload",
        "CapabilityDetector",
        "CONTRACT_SCHEMA_VERSION",
        "DeliveryArtifact",
        "ExecutionBackend",
        "FinalizationArtifact",
        "PlanArtifact",
        "PlanTaskArtifact",
        "ResumeContextArtifact",
        "ResumeRequestArtifact",
        "RequirementArtifact",
        "ReviewArtifact",
        "RuntimeResult",
        "TaskExecutionContext",
    ]
    assert hasattr(contracts_module, "PlanTaskArtifact")
    assert hasattr(contracts_module, "PlanArtifact")
    assert hasattr(contracts_module, "TaskExecutionContext")
    assert hasattr(contracts_module, "FinalizationArtifact")


class FakeProvider:
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
        return {"raw_result": "approved", "findings": [], "verification_gaps": []}

    def run_fix(self, payload):
        return {
            "delivery_summary": "fixed finding",
            "verification_evidence": ["uv run pytest"],
            "residual_risk": [],
        }

    def finalize(self, payload):
        return {"final_summary": payload}


def test_run_delivery_flow_accepts_requirement_artifact_and_returns_public_runtime_result() -> None:
    result = run_delivery_flow(
        payload=RequirementArtifact(ticket=91, goal="typed payload"),
        provider=FakeProvider(),
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert isinstance(result, RuntimeResult)
    assert result.mode == "superpowers-backed"
    assert result.completed_task_ids == ["task-1"]
    assert result.pending_task_id is None
    assert result.open_issue_summaries == []
    assert result.owner_acceptance_required is True


class ResumeProvider(FakeProvider):
    def __init__(self) -> None:
        self.review_owner_responses: list[str | None] = []

    def run_review(self, payload):
        self.review_owner_responses.append(payload.owner_response)
        return {"raw_result": "approved", "findings": [], "verification_gaps": []}


def test_resume_delivery_flow_exercises_runtime_backed_resume_path() -> None:
    provider = ResumeProvider()
    plan = PlanArtifact(
        summary="task loop",
        tasks=[PlanTaskArtifact(task_id="task-1", title="Runtime", goal="Resume runtime")],
    )

    result = resume_delivery_flow(
        request=ResumeRequestArtifact(
            previous_result=RuntimeResult(
                mode="superpowers-backed",
                final_state=ControllerState.WAITING_FOR_OWNER,
                stop_reason=StopReason.NEEDS_OWNER_DECISION,
                stage_sequence=[
                    "discussing_requirement",
                    "writing_spec",
                    "planning",
                    "running_dev",
                    "running_review",
                    "waiting_for_owner",
                ],
                pending_task_id="task-1",
                resume_context=ResumeContextArtifact(
                    plan=plan,
                    task_index=0,
                    latest_delivery=DeliveryArtifact(delivery_summary="implemented"),
                    latest_review=ReviewArtifact(
                        raw_result="owner_input_required",
                        findings=["choose rollout order"],
                        owner_decision_reason="choose rollout order",
                    ),
                ),
            ),
            owner_response="ship canary first",
        ),
        provider=provider,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert isinstance(result, RuntimeResult)
    assert result.stop_reason is StopReason.PASS
    assert provider.review_owner_responses == ["ship canary first"]
    assert result.completed_task_ids == ["task-1"]


def test_resume_delivery_flow_keeps_previous_mode_when_capabilities_change() -> None:
    provider = ResumeProvider()

    result = resume_delivery_flow(
        request={
            "previous_result": {
                "mode": "fallback",
                "final_state": "waiting_for_owner",
                "stop_reason": "needs_owner_decision",
                "stage_sequence": [
                    "discussing_requirement",
                    "writing_spec",
                    "planning",
                    "running_dev",
                    "running_review",
                    "waiting_for_owner",
                ],
                "pending_task_id": "task-1",
                "resume_context": {
                    "plan": {
                        "summary": "task loop",
                        "tasks": [
                            {
                                "task_id": "task-1",
                                "title": "Runtime",
                                "goal": "Resume runtime",
                            }
                        ],
                    },
                    "task_index": 0,
                    "latest_delivery": {"delivery_summary": "implemented"},
                    "latest_review": {
                        "raw_result": "owner_input_required",
                        "findings": ["choose rollout order"],
                        "owner_decision_reason": "choose rollout order",
                    },
                },
            },
            "owner_response": "ship canary first",
        },
        provider=provider,
        capability_detector=SimpleNamespace(has_superpowers=True),
    )

    assert result.mode == "fallback"
    assert provider.review_owner_responses == ["ship canary first"]


def test_resume_delivery_flow_rejects_unknown_previous_mode() -> None:
    with pytest.raises(ValueError, match="mode"):
        resume_delivery_flow(
            request={
                "previous_result": {
                    "mode": "mystery",
                    "final_state": "waiting_for_owner",
                    "stop_reason": "needs_owner_decision",
                    "pending_task_id": "task-1",
                    "resume_context": {
                        "plan": {
                            "summary": "task loop",
                            "tasks": [
                                {
                                    "task_id": "task-1",
                                    "title": "Runtime",
                                    "goal": "Resume runtime",
                                }
                            ],
                        },
                        "task_index": 0,
                        "latest_delivery": {"delivery_summary": "implemented"},
                        "latest_review": {
                            "raw_result": "owner_input_required",
                            "findings": ["choose rollout order"],
                            "owner_decision_reason": "choose rollout order",
                        },
                    },
                },
                "owner_response": "ship canary first",
            },
            provider=ResumeProvider(),
            capability_detector=SimpleNamespace(has_superpowers=True),
        )
