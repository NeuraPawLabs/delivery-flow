from __future__ import annotations

from dataclasses import replace

from delivery_flow.contracts import DeliveryArtifact, ReviewArtifact
from delivery_flow.contracts.models import ExecutionMetadata


class SuperpowersBackedDriver:
    def __init__(self, provider: object) -> None:
        self.provider = provider

    def _delegated_execution_metadata(self, *, stage: str) -> ExecutionMetadata:
        return ExecutionMetadata(
            backend="superpowers-backed",
            executor_kind="subagent",
            stage=stage,
        )

    def _with_execution_metadata(self, result: object, *, stage: str) -> object:
        metadata = self._delegated_execution_metadata(stage=stage)

        if isinstance(result, (DeliveryArtifact, ReviewArtifact)):
            if result.execution_metadata is not None:
                return result
            return replace(result, execution_metadata=metadata)

        if not isinstance(result, dict):
            return result

        shaped_result = dict(result)
        shaped_result.setdefault(
            "execution_metadata",
            {
                "backend": metadata.backend,
                "executor_kind": metadata.executor_kind,
                "stage": metadata.stage,
            },
        )
        return shaped_result

    def discuss_and_spec(self, payload: object) -> object:
        return self.provider.discuss_and_spec(payload)

    def plan(self, payload: object) -> object:
        return self.provider.plan(payload)

    def run_dev(self, payload: object) -> object:
        return self._with_execution_metadata(self.provider.run_dev(payload), stage="running_dev")

    def run_review(self, payload: object) -> object:
        return self._with_execution_metadata(self.provider.run_review(payload), stage="running_review")

    def run_fix(self, payload: object) -> object:
        return self._with_execution_metadata(self.provider.run_fix(payload), stage="running_fix")

    def finalize(self, payload: object) -> object:
        return self.provider.finalize(payload)
