from types import SimpleNamespace

import delivery_flow
import delivery_flow.controller as controller_module
import delivery_flow.contracts as contracts_module
import delivery_flow.runtime.engine as runtime_engine_module
import delivery_flow.runtime.models as runtime_models_module
from delivery_flow import (
    CONTRACT_SCHEMA_VERSION,
    DeliveryArtifact,
    MainAgentLoopController,
    RequirementArtifact,
    ReviewArtifact,
    RuntimeResult,
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


def test_top_level_package_exports_stable_public_contracts() -> None:
    assert delivery_flow.__all__ == [
        "CONTRACT_SCHEMA_VERSION",
        "DeliveryArtifact",
        "RequirementArtifact",
        "ReviewArtifact",
        "RuntimeResult",
        "MainAgentLoopController",
        "run_delivery_flow",
    ]
    assert callable(run_delivery_flow)
    assert DeliveryArtifact is contracts_module.DeliveryArtifact
    assert MainAgentLoopController is controller_module.MainAgentLoopController
    assert RequirementArtifact is contracts_module.RequirementArtifact
    assert ReviewArtifact is contracts_module.ReviewArtifact
    assert RuntimeResult is contracts_module.RuntimeResult
    assert run_delivery_flow is controller_module.run_delivery_flow


def test_top_level_package_does_not_export_compatibility_helpers() -> None:
    assert CONTRACT_SCHEMA_VERSION == contracts_module.CONTRACT_SCHEMA_VERSION
    assert not hasattr(delivery_flow, "build_normalized_review_snapshot")
    assert not hasattr(delivery_flow, "build_terminal_summary_snapshot")
    assert "build_normalized_review_snapshot" not in delivery_flow.__all__
    assert "build_terminal_summary_snapshot" not in delivery_flow.__all__


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
