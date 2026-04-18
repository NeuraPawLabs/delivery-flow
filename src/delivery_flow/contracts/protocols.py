from __future__ import annotations

from typing import Protocol

from delivery_flow.contracts.models import (
    DeliveryArtifact,
    FinalizationArtifact,
    PlanArtifact,
    RequirementArtifact,
    ReviewArtifact,
    TaskExecutionContext,
)


class CapabilityDetector(Protocol):
    @property
    def has_superpowers(self) -> bool: ...


class ExecutionBackend(Protocol):
    def discuss_and_spec(self, payload: RequirementArtifact | dict[str, object]) -> object: ...
    def plan(self, payload: object) -> PlanArtifact | dict[str, object]: ...
    def run_dev(
        self,
        payload: PlanArtifact | TaskExecutionContext | dict[str, object],
    ) -> DeliveryArtifact | dict[str, object]: ...
    def run_review(
        self,
        payload: DeliveryArtifact | TaskExecutionContext | dict[str, object],
    ) -> ReviewArtifact | dict[str, object]: ...
    def run_fix(self, payload: TaskExecutionContext | dict[str, object]) -> DeliveryArtifact | dict[str, object]: ...
    def finalize(self, payload: object) -> FinalizationArtifact | dict[str, object]: ...
