from typing import get_args, get_type_hints

from delivery_flow.adapters.fallback import FallbackAdapter
from delivery_flow.adapters.superpowers import SuperpowersAdapter
from delivery_flow.contracts import (
    DeliveryArtifact,
    FinalizationArtifact,
    PlanArtifact,
    RequirementArtifact,
    ReviewArtifact,
    TaskExecutionContext,
)
from delivery_flow.contracts.protocols import ExecutionBackend


class FakeProvider:
    def __init__(self, review_result="approved"):
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


def test_superpowers_adapter_exposes_runtime_action_surface() -> None:
    adapter = SuperpowersAdapter(provider=FakeProvider())

    assert callable(adapter.discuss_and_spec)
    assert callable(adapter.plan)
    assert callable(adapter.run_dev)
    assert callable(adapter.run_review)
    assert callable(adapter.run_fix)
    assert callable(adapter.finalize)


def test_fallback_adapter_exposes_runtime_action_surface() -> None:
    adapter = FallbackAdapter(provider=FakeProvider())

    assert callable(adapter.discuss_and_spec)
    assert callable(adapter.plan)
    assert callable(adapter.run_dev)
    assert callable(adapter.run_review)
    assert callable(adapter.run_fix)
    assert callable(adapter.finalize)


def test_adapters_forward_payloads_without_adding_semantics() -> None:
    payload = {"ticket": 204}
    provider = FakeProvider()

    for adapter_type in (SuperpowersAdapter, FallbackAdapter):
        adapter = adapter_type(provider=provider)
        assert adapter.discuss_and_spec(payload) == provider.discuss_and_spec(payload)
        assert adapter.plan(payload) == provider.plan(payload)
        assert adapter.run_dev(payload) == provider.run_dev(payload)
        assert adapter.run_review(payload) == provider.run_review(payload)
        assert adapter.run_fix(payload) == provider.run_fix(payload)
        assert adapter.finalize(payload) == provider.finalize(payload)


def test_adapters_match_execution_backend_protocol_type_surface() -> None:
    protocol_hints = {
        "discuss_and_spec": get_type_hints(ExecutionBackend.discuss_and_spec),
        "plan": get_type_hints(ExecutionBackend.plan),
        "run_dev": get_type_hints(ExecutionBackend.run_dev),
        "run_review": get_type_hints(ExecutionBackend.run_review),
        "run_fix": get_type_hints(ExecutionBackend.run_fix),
        "finalize": get_type_hints(ExecutionBackend.finalize),
    }
    superpowers_init_hints = get_type_hints(SuperpowersAdapter.__init__)
    fallback_init_hints = get_type_hints(FallbackAdapter.__init__)

    assert superpowers_init_hints["provider"] is ExecutionBackend
    assert fallback_init_hints["provider"] is ExecutionBackend

    for adapter_type in (SuperpowersAdapter, FallbackAdapter):
        discuss_hints = get_type_hints(adapter_type.discuss_and_spec)
        plan_hints = get_type_hints(adapter_type.plan)
        dev_hints = get_type_hints(adapter_type.run_dev)
        review_hints = get_type_hints(adapter_type.run_review)
        fix_hints = get_type_hints(adapter_type.run_fix)
        finalize_hints = get_type_hints(adapter_type.finalize)

        assert set(get_args(discuss_hints["payload"])) == {RequirementArtifact, dict[str, object]}
        assert set(get_args(discuss_hints["return"])) == set(get_args(protocol_hints["discuss_and_spec"]["return"]))
        assert set(get_args(plan_hints["return"])) == {PlanArtifact, dict[str, object]}
        assert set(get_args(dev_hints["payload"])) == {PlanArtifact, TaskExecutionContext, dict[str, object]}
        assert set(get_args(dev_hints["return"])) == {DeliveryArtifact, dict[str, object]}
        assert set(get_args(review_hints["payload"])) == {DeliveryArtifact, TaskExecutionContext, dict[str, object]}
        assert set(get_args(review_hints["return"])) == {ReviewArtifact, dict[str, object]}
        assert set(get_args(fix_hints["payload"])) == {TaskExecutionContext, dict[str, object]}
        assert set(get_args(fix_hints["return"])) == {DeliveryArtifact, dict[str, object]}
        assert set(get_args(finalize_hints["return"])) == {FinalizationArtifact, dict[str, object]}
