from types import SimpleNamespace
from typing import get_args, get_type_hints

import pytest

from delivery_flow.controller import (
    BlockerIdentity,
    ControllerState,
    MainAgentLoopController,
    NormalizedReviewResult,
    run_delivery_flow,
)
from delivery_flow.runtime.engine import DeliveryFlowRuntime

from delivery_flow.contracts import (
    DeliveryArtifact,
    FinalizationArtifact,
    PlanArtifact,
    RequirementArtifact,
    ReviewArtifact,
    TaskExecutionContext,
)
from delivery_flow.contracts.protocols import CapabilityDetector, ExecutionBackend


def test_initial_controller_state_is_discussing_requirement() -> None:
    controller = MainAgentLoopController()

    assert controller.state is ControllerState.DISCUSSING_REQUIREMENT


def test_select_mode_chooses_superpowers_backed_when_capability_is_available() -> None:
    detector = SimpleNamespace(has_superpowers=True)
    controller = MainAgentLoopController(capability_detector=detector)

    mode = controller.select_mode()

    assert mode == "superpowers-backed"
    assert controller.mode == "superpowers-backed"


def test_select_mode_falls_back_when_superpowers_capability_is_unavailable() -> None:
    detector = SimpleNamespace(has_superpowers=False)
    controller = MainAgentLoopController(capability_detector=detector)

    mode = controller.select_mode()

    assert mode == "fallback"
    assert controller.mode == "fallback"


def test_select_mode_rejects_implicit_guessing_when_detector_is_missing() -> None:
    controller = MainAgentLoopController()

    with pytest.raises(RuntimeError, match="Capability detector is required"):
        controller.select_mode()


def test_mode_banner_is_explicit_after_selection() -> None:
    detector = SimpleNamespace(has_superpowers=True)
    controller = MainAgentLoopController(capability_detector=detector)

    controller.select_mode()

    assert controller.mode_banner() == "mode=superpowers-backed"


def test_review_result_normalization_maps_superpowers_specific_results() -> None:
    controller = MainAgentLoopController()

    assert controller.normalize_review_result("approved") is NormalizedReviewResult.PASS
    assert controller.normalize_review_result("changes_requested") is NormalizedReviewResult.BLOCKER
    assert (
        controller.normalize_review_result("owner_input_required")
        is NormalizedReviewResult.NEEDS_OWNER_DECISION
    )


def test_review_result_normalization_rejects_unknown_raw_results() -> None:
    controller = MainAgentLoopController()

    with pytest.raises(RuntimeError, match="Unknown raw review result"):
        controller.normalize_review_result("shrug")


def test_blocker_identity_derivation_extracts_controller_owned_fields() -> None:
    controller = MainAgentLoopController()

    identity = controller.derive_blocker_identity(
        {
            "contract_area": "stop-rule handling",
            "failure_kind": "incorrect behavior",
            "expected_resolution": "same blocker stops after two cycles",
            "backend_note": "wording that should not matter",
        }
    )

    assert identity == BlockerIdentity(
        contract_area="stop-rule handling",
        failure_kind="incorrect behavior",
        expected_resolution="same blocker stops after two cycles",
    )


def test_blocker_identity_derivation_requires_all_identity_fields() -> None:
    controller = MainAgentLoopController()

    with pytest.raises(RuntimeError, match="available evidence"):
        controller.derive_blocker_identity(
            {
                "contract_area": "required verification evidence",
                "failure_kind": "verification gap",
            }
        )


def test_blocker_identity_derivation_accepts_review_artifact() -> None:
    controller = MainAgentLoopController()

    identity = controller.derive_blocker_identity(
        ReviewArtifact(
            raw_result="changes_requested",
            contract_area="trace",
            failure_kind="missing evidence",
            expected_resolution="record transitions",
        )
    )

    assert identity == BlockerIdentity(
        contract_area="trace",
        failure_kind="missing evidence",
        expected_resolution="record transitions",
    )


def test_controller_and_runtime_use_contract_protocols() -> None:
    controller_hints = get_type_hints(run_delivery_flow)
    runtime_hints = get_type_hints(DeliveryFlowRuntime.__init__)
    derive_hints = get_type_hints(MainAgentLoopController.derive_blocker_identity)
    engine_derive_hints = get_type_hints(DeliveryFlowRuntime.derive_blocker_identity)
    plan_hints = get_type_hints(ExecutionBackend.plan)
    protocol_hints = get_type_hints(ExecutionBackend.run_review)
    dev_hints = get_type_hints(ExecutionBackend.run_dev)
    fix_hints = get_type_hints(ExecutionBackend.run_fix)
    finalize_hints = get_type_hints(ExecutionBackend.finalize)
    discuss_hints = get_type_hints(ExecutionBackend.discuss_and_spec)

    assert controller_hints["capability_detector"] is CapabilityDetector
    assert controller_hints["provider"] is ExecutionBackend
    assert set(get_args(runtime_hints["adapter"])) == {ExecutionBackend, type(None)}
    assert set(get_args(runtime_hints["capability_detector"])) == {CapabilityDetector, type(None)}
    assert set(get_args(derive_hints["review_payload"])) == {ReviewArtifact, dict[str, str]}
    assert set(get_args(engine_derive_hints["review_payload"])) == {ReviewArtifact, dict[str, str]}
    assert set(get_args(discuss_hints["payload"])) == {RequirementArtifact, dict[str, object]}
    assert set(get_args(plan_hints["return"])) == {PlanArtifact, dict[str, object]}
    assert set(get_args(dev_hints["payload"])) == {PlanArtifact, TaskExecutionContext, dict[str, object]}
    assert set(get_args(dev_hints["return"])) == {DeliveryArtifact, dict[str, object]}
    assert set(get_args(protocol_hints["payload"])) == {DeliveryArtifact, TaskExecutionContext, dict[str, object]}
    assert set(get_args(protocol_hints["return"])) == {ReviewArtifact, dict[str, object]}
    assert set(get_args(fix_hints["payload"])) == {TaskExecutionContext, dict[str, object]}
    assert set(get_args(fix_hints["return"])) == {DeliveryArtifact, dict[str, object]}
    assert set(get_args(finalize_hints["return"])) == {FinalizationArtifact, dict[str, object]}
