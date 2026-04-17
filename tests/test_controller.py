from types import SimpleNamespace

import pytest

from delivery_flow.controller import (
    BlockerIdentity,
    ControllerState,
    MainAgentLoopController,
    NormalizedReviewResult,
)


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
