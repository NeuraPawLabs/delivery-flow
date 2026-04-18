from __future__ import annotations

from delivery_flow.contracts import (
    DeliveryArtifact,
    FinalizationArtifact,
    PlanArtifact,
    RequirementArtifact,
    ReviewArtifact,
    TaskExecutionContext,
)
from delivery_flow.contracts.protocols import ExecutionBackend


class FallbackAdapter:
    def __init__(self, provider: ExecutionBackend) -> None:
        self.provider = provider

    def discuss_and_spec(self, payload: RequirementArtifact | dict[str, object]) -> object:
        return self.provider.discuss_and_spec(payload)

    def plan(self, payload: object) -> PlanArtifact | dict[str, object]:
        return self.provider.plan(payload)

    def run_dev(
        self,
        payload: PlanArtifact | TaskExecutionContext | dict[str, object],
    ) -> DeliveryArtifact | dict[str, object]:
        return self.provider.run_dev(payload)

    def run_review(
        self,
        payload: DeliveryArtifact | TaskExecutionContext | dict[str, object],
    ) -> ReviewArtifact | dict[str, object]:
        return self.provider.run_review(payload)

    def run_fix(self, payload: TaskExecutionContext | dict[str, object]) -> DeliveryArtifact | dict[str, object]:
        return self.provider.run_fix(payload)

    def finalize(self, payload: object) -> FinalizationArtifact | dict[str, object]:
        return self.provider.finalize(payload)
