from __future__ import annotations

from delivery_flow.contracts import RequirementArtifact, ReviewArtifact, RuntimeResult
from delivery_flow.contracts.protocols import CapabilityDetector, ExecutionBackend
from delivery_flow.adapters.fallback import FallbackAdapter
from delivery_flow.adapters.superpowers import SuperpowersAdapter
from delivery_flow.runtime.engine import DeliveryFlowRuntime
from delivery_flow.runtime.models import (
    BlockerIdentity,
    ControllerState,
    NormalizedReviewResult,
    StopReason,
)


class MainAgentLoopController:
    def __init__(self, capability_detector: CapabilityDetector | None = None) -> None:
        self.capability_detector = capability_detector
        self.state = ControllerState.DISCUSSING_REQUIREMENT
        self.mode: str | None = None

    def select_mode(self) -> str:
        runtime = DeliveryFlowRuntime(adapter=None, capability_detector=self.capability_detector)
        self.mode = runtime.select_mode()
        return self.mode

    def mode_banner(self) -> str:
        if self.mode is None:
            raise RuntimeError("Mode must be selected before banner emission")

        return f"mode={self.mode}"

    def normalize_review_result(self, raw_result: str) -> NormalizedReviewResult:
        runtime = DeliveryFlowRuntime(adapter=None, capability_detector=self.capability_detector)
        return runtime.normalize_review_result(raw_result)

    def derive_blocker_identity(self, review_payload: ReviewArtifact | dict[str, str]) -> BlockerIdentity:
        runtime = DeliveryFlowRuntime(adapter=None, capability_detector=self.capability_detector)
        return runtime.derive_blocker_identity(review_payload)


def run_delivery_flow(
    *,
    payload: RequirementArtifact | dict[str, object],
    provider: ExecutionBackend,
    capability_detector: CapabilityDetector,
) -> RuntimeResult:
    selector = MainAgentLoopController(capability_detector=capability_detector)
    mode = selector.select_mode()
    adapter = SuperpowersAdapter(provider=provider) if mode == "superpowers-backed" else FallbackAdapter(provider=provider)
    runtime = DeliveryFlowRuntime(adapter=adapter, capability_detector=capability_detector)
    runtime.mode = mode
    return runtime.run(payload)


__all__ = [
    "BlockerIdentity",
    "ControllerState",
    "DeliveryFlowRuntime",
    "MainAgentLoopController",
    "NormalizedReviewResult",
    "StopReason",
    "run_delivery_flow",
]
